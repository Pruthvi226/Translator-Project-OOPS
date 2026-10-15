# Reproducible evaluation

No model quality results have been measured or claimed. Unit-test fixtures are
metric correctness checks and must never be presented as model benchmarks.

Obtain FLORES-200 devtest data from its publisher, review its license and record
the dataset version/split. Keep dev for prompt tuning and devtest held out.
Use aligned language files with `python -m evaluation.prepare_flores source.txt
reference.txt --src-lang en --target-lang hi --out evaluation/flores-en-hi.jsonl`.
Do not include private user translations in published results.

Install API/dev dependencies. Explicitly enable only the providers you intend to
evaluate. NLLB is optional and has a noncommercial model license. Run:

```sh
python -m evaluation.run evaluation/flores-en-hi.jsonl --providers gemini nllb --concurrency 1 --out evaluation/results/en-hi
```

This command makes real calls and can incur charges. Provider selection is strict;
fallback is disabled to avoid misattributing quality. Record hardware, model ID,
SDK lockfile, warmup policy, dataset version and cost rates with the artifacts.
Make separate cold/warm runs. Throughput is observed requests per total run time,
not the inverse of median latency. Concurrent runs share the same bounded service.
Failure latency is included; quality uses successful reference-bearing predictions
and reports its denominator. Never compare results with different splits/tokenizers.

To score saved JSONL predictions, omit `--providers`. Each record has `source`,
`reference`, `hypothesis`, `provider`, `src_lang`, `target_lang`, and optionally
`latency_ms`, `error`, `fallback`, `estimated_cost_usd`, `run_elapsed_seconds`,
`speech_reference`/`transcription`, `ocr_reference`/`ocr_text`. Scores are BLEU,
chrF, WER and CER as applicable. BLEU uses zh segmentation for Chinese, ja-mecab
for Japanese (install `sacrebleu[ja]`), and 13a otherwise. Tokenizer signatures
are saved. WER/CER currently use jiwer's case-sensitive defaults; document any
normalization before comparison. Missing measurements remain null.

Optional COMET: install `unbabel-comet`, accept the checkpoint license/download
requirements and add `--comet`. This is deliberately excluded from normal CI.
Reports contain JSON, Markdown, a chrF chart and input SHA256 manifest; prediction
files may contain source data, so keep them private unless licensed for release.
