import importlib
import pytest


@pytest.fixture
def legacy(monkeypatch):
    module = importlib.import_module('app')
    monkeypatch.setattr(module, 'gemini', None)
    monkeypatch.setattr(module, 'providers', {})
    module.buckets.clear()
    return module, module.app.test_client()


def test_legacy_ui_and_safe_failures(legacy):
    _, client = legacy
    assert client.get('/').status_code == 200
    assert client.get('/ai-status').json['connectivity_verified'] is False
    assert client.post('/translate', json=['invalid']).status_code == 400
    assert client.post('/translate', json={'text': 'a' * 5001}).status_code == 400
    assert client.post('/translate', json={'text': 'Hello'}).status_code == 503


def test_legacy_audio_is_not_public_file(legacy, monkeypatch):
    module, client = legacy
    monkeypatch.setattr(module, 'synthesize', lambda *args: b'audio')
    response = client.post('/tts', json={'text': 'Hello', 'lang': 'en'})
    assert response.status_code == 200
    assert response.json['audio_url'].startswith('data:audio/mpeg;base64,')
    assert response.headers['Cache-Control'] == 'no-store'
