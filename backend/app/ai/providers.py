"""Adapters load optional ML dependencies only when explicitly configured."""
import asyncio
import json
import threading
import subprocess
import sys
from dataclasses import dataclass
from .prompts import TRANSLATOR, TUTOR
from ..schemas import LANGUAGES, TranslationOutput, TutorOutput


class ProviderUnavailable(Exception):
    pass


@dataclass
class Completion:
    output: TranslationOutput
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float | None = None


class GeminiProvider:
    name = 'gemini'
    supports_tone = True

    def __init__(self, settings):
        from google import genai
        self.settings = settings
        self.client = genai.Client(api_key=settings.gemini_api_key,
                                   http_options={'timeout': int(settings.provider_timeout * 1000),
                                                 'retry_options': {'attempts': 1}})

    async def structured(self, instruction, payload, schema):
        from google.genai import types
        response = await self.client.aio.models.generate_content(
            model=self.settings.gemini_model,
            contents=json.dumps(payload, ensure_ascii=False),
            config=types.GenerateContentConfig(system_instruction=instruction,
                response_mime_type='application/json', response_schema=schema, temperature=0.2))
        parsed = schema.model_validate_json(response.text or '')
        return parsed, response.usage_metadata

    async def translate(self, text, src, target, tone):
        output, usage = await self.structured(TRANSLATOR,
            {'source_language': src, 'target_language': target, 'tone': tone, 'text': text}, TranslationOutput)
        incoming = (getattr(usage, 'prompt_token_count', 0) or 0)
        outgoing = (getattr(usage, 'candidates_token_count', 0) or 0) + (getattr(usage, 'thoughts_token_count', 0) or 0)
        prices = (self.settings.gemini_input_usd_per_million, self.settings.gemini_output_usd_per_million)
        cost = (incoming * prices[0] + outgoing * prices[1]) / 1e6 if None not in prices else None
        return Completion(output, incoming, outgoing, cost)

    async def tutor(self, payload):
        result, _ = await self.structured(TUTOR, payload, TutorOutput)
        return result


class DeepTranslatorProvider:
    name = 'deep-translator'
    supports_tone = False

    def __init__(self, timeout=30):
        self.timeout = timeout

    def _translate(self, text, src, target):
        # The library has no socket timeout. Isolate it in a killable process;
        # subprocess.run terminates and reaps the child when the deadline expires.
        code = ('import json,sys; from deep_translator import GoogleTranslator; '
                'p=json.load(sys.stdin); '
                'print(json.dumps(GoogleTranslator(source=p["src"],target=p["target"]).translate(p["text"])))')
        process = subprocess.run([sys.executable, '-c', code],
            input=json.dumps({'src': src, 'target': target, 'text': text}),
            capture_output=True, text=True, encoding='utf-8', timeout=self.timeout,
            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), check=True)
        detected = src
        if src == 'auto':
            from langdetect import detect, DetectorFactory
            DetectorFactory.seed = 0
            try:
                detected = detect(text)
            except Exception:
                detected = 'und'
        return Completion(TranslationOutput(translated_text=json.loads(process.stdout), detected_language=detected))

    async def translate(self, text, src, target, tone):
        return await asyncio.to_thread(self._translate, text, src, target)


class NLLBProvider:
    name = 'nllb'
    supports_tone = False

    def __init__(self):
        self.lock = threading.Lock()
        self.model = None

    def _translate(self, text, src, target):
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        if src == 'auto':
            from langdetect import detect
            src = detect(text)
            src = 'zh-CN' if src == 'zh-cn' else src
        if src not in LANGUAGES:
            raise ProviderUnavailable('Source language not supported by NLLB adapter')
        with self.lock:
            model_id = 'facebook/nllb-200-distilled-600M'
            if self.model is None:
                self.tokenizer = AutoTokenizer.from_pretrained(model_id)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(model_id).eval()
            self.tokenizer.src_lang = LANGUAGES[src][1]
            inputs = self.tokenizer(text, return_tensors='pt', truncation=False)
            if inputs.input_ids.shape[1] > 512:
                raise ProviderUnavailable('Segment exceeds NLLB token limit; reduce chunk size')
            with torch.inference_mode():
                result = self.model.generate(**inputs, forced_bos_token_id=self.tokenizer.convert_tokens_to_ids(
                    LANGUAGES[target][1]), max_new_tokens=512)
            output = self.tokenizer.batch_decode(result, skip_special_tokens=True)[0]
        return Completion(TranslationOutput(translated_text=output, detected_language=src))

    async def translate(self, text, src, target, tone):
        return await asyncio.to_thread(self._translate, text, src, target)


def build_providers(settings):
    providers = {}
    if settings.gemini_api_key:
        providers['gemini'] = GeminiProvider(settings)
    if settings.enable_deep_translator:
        providers['deep-translator'] = DeepTranslatorProvider(max(1, settings.provider_timeout - 1))
    if settings.enable_nllb:
        providers['nllb'] = NLLBProvider()
    return providers
