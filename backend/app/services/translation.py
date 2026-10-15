import asyncio
import logging
import re
from time import perf_counter
from ..ai.providers import ProviderUnavailable

logger = logging.getLogger('fluentflow')


def segment(text, limit=1200):
    """Lossless paragraph/line segmentation, then sentence/space boundaries."""
    result = []
    for block in re.split(r'(\n+)', text):
        if not block:
            continue
        if block.isspace():
            result.append(block)
            continue
        while len(block) > limit:
            boundary = max(block.rfind('. ', 0, limit), block.rfind('。', 0, limit),
                           block.rfind(' ', 0, limit))
            boundary = boundary + 1 if boundary > limit // 2 else limit
            result.append(block[:boundary])
            block = block[boundary:]
        if block:
            result.append(block)
    return result


class TranslationService:
    def __init__(self, settings, providers):
        self.settings = settings
        self.providers = providers
        self.gate = asyncio.Semaphore(4)
        self.pending = set()

    async def _call(self, provider, text, req):
        # Gate remains held until the actual task finishes, including timed out threads.
        async with self.gate:
            return await provider.translate(text, req.src_lang, req.target_lang, req.tone)

    async def translate(self, req):
        started = perf_counter()
        if len(self.pending) >= 8:
            raise ProviderUnavailable('Translation capacity reached; retry shortly')
        order = [p.strip() for p in self.settings.provider_order.split(',') if p.strip()]
        if req.provider != 'auto':
            order = [req.provider] + ([p for p in order if p != req.provider] if req.allow_fallback else [])
        elif not req.allow_fallback:
            order = order[:1]
        candidates = [self.providers[p] for p in order if p in self.providers]
        if not candidates:
            raise ProviderUnavailable('No translation provider is configured')
        failures = 0
        output, used, warnings = [], [], []
        input_tokens = output_tokens = 0
        costs = []
        detected = req.src_lang
        for chunk in segment(req.text, limit=400 if any(p.name == 'nllb' for p in candidates) else 1200):
            if chunk.isspace():
                output.append(chunk)
                continue
            completed = False
            for provider in candidates:
                for attempt in range(self.settings.provider_retries + 1):
                    task = asyncio.create_task(self._call(provider, chunk, req))
                    self.pending.add(task)
                    def consume(done):
                        self.pending.discard(done)
                        if not done.cancelled():
                            done.exception()
                    task.add_done_callback(consume)
                    try:
                        result = await asyncio.wait_for(asyncio.shield(task), self.settings.provider_timeout)
                        leading = chunk[:len(chunk) - len(chunk.lstrip())]
                        trailing = chunk[len(chunk.rstrip()):]
                        output.append(leading + result.output.translated_text.strip() + trailing)
                        detected = result.output.detected_language
                        used.append(provider.name)
                        input_tokens += result.input_tokens
                        output_tokens += result.output_tokens
                        costs.append(result.estimated_cost_usd)
                        if not provider.supports_tone:
                            warnings.append(f'{provider.name} does not support tone control.')
                        completed = True
                        break
                    except Exception as exc:
                        failures += 1
                        logger.warning('provider_failure', extra={'provider': provider.name, 'error_type': type(exc).__name__})
                        if isinstance(exc, TimeoutError):
                            break
                        if attempt < self.settings.provider_retries:
                            await asyncio.sleep(0.2 * 2**attempt)
                if completed:
                    break
            if not completed:
                raise ProviderUnavailable('Translation providers are temporarily unavailable')
        return {'translated_text': ''.join(output), 'detected_language': detected,
                'providers': sorted(set(used)), 'fallback': bool(used and any(p != order[0] for p in used)),
                'provider_failures': failures, 'latency_ms': round((perf_counter() - started) * 1000, 2),
                'input_tokens': input_tokens, 'output_tokens': output_tokens,
                'estimated_cost_usd': sum(costs) if costs and all(c is not None for c in costs) else None,
                'warnings': sorted(set(warnings))}
