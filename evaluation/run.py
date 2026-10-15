"""Reference-based quality scoring and provider benchmarking; no synthetic scores."""
import argparse
import asyncio
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from time import perf_counter

import numpy as np


def score(rows, elapsed=None, comet=False):
    from sacrebleu.metrics import BLEU, CHRF
    from jiwer import cer, wer
    reports = []
    groups = defaultdict(list)
    for row in rows:
        groups[(row.get('provider', 'unknown'), row.get('src_lang', '?'), row.get('target_lang', '?'))].append(row)
    for (provider, src, target), samples in groups.items():
        valid = [s for s in samples if not s.get('error') and s.get('hypothesis')]
        translation = [s for s in valid if s.get('reference')]
        report = {'provider': provider, 'src_lang': src, 'target_lang': target,
                  'requests': len(samples), 'scored': len(translation),
                  'failure_rate': sum(bool(s.get('error')) for s in samples) / len(samples),
                  'fallback_rate': sum(bool(s.get('fallback')) for s in valid) / len(valid) if valid else None,
                  'bleu': None, 'chrf': None, 'comet': None, 'wer': None, 'cer': None,
                  'p50_ms': None, 'p95_ms': None, 'requests_per_second': None,
                  'estimated_cost_per_request_usd': None}
        if translation:
            tokenizer = 'zh' if target in {'zh', 'zh-CN'} else 'ja-mecab' if target == 'ja' else '13a'
            bleu = BLEU(tokenize=tokenizer)
            report['bleu'] = bleu.corpus_score([s['hypothesis'] for s in translation], [[s['reference'] for s in translation]]).score
            report['bleu_signature'] = str(bleu.get_signature())
            chrf = CHRF()
            report['chrf'] = chrf.corpus_score([s['hypothesis'] for s in translation], [[s['reference'] for s in translation]]).score
            report['chrf_signature'] = str(chrf.get_signature())
        speech = [s for s in samples if s.get('speech_reference') is not None and s.get('transcription') is not None]
        ocr = [s for s in samples if s.get('ocr_reference') is not None and s.get('ocr_text') is not None]
        if speech:
            report['wer'] = wer([s['speech_reference'] for s in speech], [s['transcription'] for s in speech])
        if ocr:
            report['cer'] = cer([s['ocr_reference'] for s in ocr], [s['ocr_text'] for s in ocr])
        latencies = [s['latency_ms'] for s in samples if s.get('latency_ms') is not None]
        if latencies:
            report['p50_ms'], report['p95_ms'] = [float(x) for x in np.percentile(latencies, [50, 95])]
        durations = [s.get('run_elapsed_seconds') for s in samples if s.get('run_elapsed_seconds')]
        duration = max(durations) if durations else elapsed
        if duration:
            report['requests_per_second'] = len(samples) / duration
        costs = [s['estimated_cost_usd'] for s in valid if s.get('estimated_cost_usd') is not None]
        if costs and len(costs) == len(valid):
            report['estimated_cost_per_request_usd'] = sum(costs) / len(costs)
        if comet and translation:
            from comet import download_model, load_from_checkpoint
            model = load_from_checkpoint(download_model('Unbabel/wmt22-comet-da'))
            prediction = model.predict([{'src': s['source'], 'mt': s['hypothesis'], 'ref': s['reference']} for s in translation], batch_size=8, gpus=0)
            report['comet'] = float(prediction.system_score)
        reports.append(report)
    return reports


async def benchmark(rows, providers, concurrency):
    from backend.app.ai.providers import build_providers
    from backend.app.config import get_settings
    from backend.app.schemas import TranslationRequest
    from backend.app.services.translation import TranslationService
    settings = get_settings()
    adapters = build_providers(settings)
    gate = asyncio.Semaphore(concurrency)
    output = []
    for provider in providers:
        service = TranslationService(settings, adapters)
        started = perf_counter()
        async def one(row):
            async with gate:
                record = {**row, 'provider': provider}
                begin = perf_counter()
                try:
                    result = await service.translate(TranslationRequest(text=row['source'], src_lang=row['src_lang'],
                        target_lang=row['target_lang'], provider=provider, allow_fallback=False))
                    record.update(hypothesis=result['translated_text'], latency_ms=result['latency_ms'],
                                  fallback=result['fallback'], estimated_cost_usd=result['estimated_cost_usd'])
                except Exception as exc:
                    record.update(error=type(exc).__name__, latency_ms=(perf_counter() - begin) * 1000)
                return record
        measured = await asyncio.gather(*(one(row) for row in rows))
        elapsed = perf_counter() - started
        for row in measured:
            row['run_elapsed_seconds'] = elapsed
        output.extend(measured)
    for adapter in adapters.values():
        if hasattr(adapter, 'client'):
            await adapter.client.aio.aclose()
            adapter.client.close()
    return output


def artifacts(reports, output):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    output.mkdir(parents=True, exist_ok=True)
    (output / 'report.json').write_text(json.dumps(reports, indent=2), encoding='utf-8')
    columns = ['provider', 'src_lang', 'target_lang', 'requests', 'scored', 'bleu', 'chrf', 'comet', 'wer', 'cer', 'p50_ms', 'p95_ms', 'requests_per_second', 'failure_rate', 'fallback_rate', 'estimated_cost_per_request_usd']
    table = '| ' + ' | '.join(columns) + ' |\n|' + '|'.join(['---'] * len(columns)) + '|\n'
    table += '\n'.join('| ' + ' | '.join('not measured' if r.get(c) is None else str(round(r[c], 4)) if isinstance(r[c], float) else str(r[c]) for c in columns) + ' |' for r in reports)
    (output / 'report.md').write_text(table, encoding='utf-8')
    measured = [r for r in reports if r['chrf'] is not None]
    if measured:
        figure, axis = plt.subplots(figsize=(max(6, len(measured) * 1.6), 4))
        axis.bar([f"{r['provider']}\n{r['src_lang']} → {r['target_lang']}" for r in measured], [r['chrf'] for r in measured], color='#197c61')
        axis.set_ylabel('chrF (0–100)')
        axis.set_ylim(0, 100)
        axis.set_title('Reference-based translation evaluation')
        figure.tight_layout()
        figure.savefig(output / 'quality.png', dpi=160)
        plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data', type=Path, help='JSONL source/reference records or measured predictions')
    parser.add_argument('--providers', nargs='+', help='Make REAL provider calls (can incur cost); otherwise score existing hypotheses')
    parser.add_argument('--concurrency', type=int, choices=range(1, 9), default=1)
    parser.add_argument('--comet', action='store_true')
    parser.add_argument('--out', type=Path, default=Path('evaluation/results'))
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.data.read_text(encoding='utf-8').splitlines() if line.strip()]
    if not rows:
        parser.error('Dataset is empty')
    if args.providers:
        rows = asyncio.run(benchmark(rows, args.providers, args.concurrency))
    reports = score(rows, comet=args.comet)
    artifacts(reports, args.out)
    (args.out / 'predictions.jsonl').write_text('\n'.join(json.dumps(r, ensure_ascii=False) for r in rows), encoding='utf-8')
    (args.out / 'manifest.json').write_text(json.dumps({'dataset_sha256': hashlib.sha256(args.data.read_bytes()).hexdigest(),
        'created_at': datetime.now(timezone.utc).isoformat(), 'concurrency': args.concurrency,
        'providers': args.providers, 'comet': args.comet, 'dataset': str(args.data),
        'warning': 'Scores describe only the supplied dataset, not general translation quality.'}, indent=2), encoding='utf-8')
    print(f'Wrote measured artifacts to {args.out}')


if __name__ == '__main__':
    main()
