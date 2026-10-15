"""Preserved Flask UI for local use. Production entrypoint: backend.app.main."""
import asyncio
import base64
from collections import defaultdict, deque
import json
import os
from time import monotonic
from flask import Flask, jsonify, render_template, request
from dotenv import load_dotenv
from backend.app.ai.prompts import TRANSLATOR, TUTOR
from backend.app.ai.providers import build_providers
from backend.app.config import Settings
from backend.app.schemas import TranslationOutput, TutorOutput
from backend.app.services.media import synthesize

load_dotenv()
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100000
settings = Settings()
providers = build_providers(settings)
gemini = providers.get('gemini')
buckets = defaultdict(deque)


@app.before_request
def limit_requests():
    if request.method != 'POST':
        return None
    stamp = monotonic()
    bucket = buckets[request.remote_addr]
    while bucket and stamp - bucket[0] > 60:
        bucket.popleft()
    if len(bucket) >= 30:
        return jsonify(error='Request limit reached. Try again in a minute.'), 429
    bucket.append(stamp)


@app.after_request
def private_response(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-store'
    return response


def data():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValueError('JSON object required')
    for value in payload.values():
        if isinstance(value, str) and len(value) > 5000:
            raise ValueError('Text exceeds 5,000 characters')
    return payload


def required(payload, *keys):
    for key in keys:
        if not isinstance(payload.get(key), str) or not payload[key].strip():
            raise ValueError('Required text is missing')


def structured(instruction, payload, schema):
    if not gemini:
        raise RuntimeError('Gemini not configured')
    from google.genai import types
    response = gemini.client.models.generate_content(model=settings.gemini_model,
        contents=json.dumps(payload, ensure_ascii=False),
        config=types.GenerateContentConfig(system_instruction=instruction,
            response_mime_type='application/json', response_schema=schema, temperature=0.2))
    return schema.model_validate_json(response.text or '')


@app.errorhandler(ValueError)
def invalid_input(exc):
    return jsonify(error='Invalid input. Check required fields and length limits.'), 400


@app.route('/')
def index():
    return render_template('index.html')


@app.get('/ai-status')
def ai_status():
    return jsonify(unlocked=bool(gemini), mode='Gemini configured' if gemini else 'Provider setup required',
                   connectivity_verified=False)


@app.post('/translate')
def translate():
    payload = data()
    required(payload, 'text')
    src = payload.get('src_lang', 'auto')
    target = payload.get('target_lang', 'en')
    if not isinstance(src, str) or not isinstance(target, str):
        raise ValueError('Invalid language')
    if gemini and payload.get('use_ai'):
        try:
            result = structured(TRANSLATOR, {'text': payload['text'], 'source_language': src,
                'target_language': target, 'tone': payload.get('tone', 'professional')}, TranslationOutput)
            return jsonify(translated_text=result.translated_text, method='gemini', tone=payload.get('tone'))
        except Exception:
            app.logger.warning('Legacy Gemini translation failed')
    if 'deep-translator' in providers:
        try:
            result = asyncio.run(asyncio.wait_for(providers['deep-translator'].translate(
                payload['text'], src, target, 'professional'), settings.provider_timeout))
            return jsonify(translated_text=result.output.translated_text, method='deep-translator', tone='default')
        except Exception:
            app.logger.warning('Legacy fallback translation failed')
    return jsonify(error='Translation unavailable. Configure Gemini or explicitly enable Deep Translator.'), 503


@app.post('/ai-insights')
def insights():
    payload = data()
    required(payload, 'original_text', 'translated_text')
    try:
        reply = structured(TUTOR, {**payload, 'question': 'Explain grammar, vocabulary and cultural nuances.'}, TutorOutput)
        return jsonify(insights=reply.answer + '\n\n' + '\n'.join(reply.alternatives + reply.exercises))
    except Exception:
        return jsonify(error='Language insights are currently unavailable.'), 503


@app.post('/chat')
def chat():
    payload = data()
    required(payload, 'original_text', 'translated_text', 'question')
    history = payload.get('chat_history', [])
    if not isinstance(history, list) or len(history) > 40:
        raise ValueError('Invalid history')
    payload['chat_history'] = history[-6:]
    try:
        reply = structured(TUTOR, payload, TutorOutput)
        return jsonify(reply=reply.answer)
    except Exception:
        return jsonify(error='Language tutor is currently unavailable.'), 503


@app.post('/tts')
def tts():
    payload = data()
    required(payload, 'text')
    try:
        audio = synthesize(payload['text'], payload.get('lang', 'en'))
        return jsonify(audio_url='data:audio/mpeg;base64,' + base64.b64encode(audio).decode('ascii'))
    except Exception:
        return jsonify(error='Speech synthesis is unavailable for this language.'), 503


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')), debug=False)
