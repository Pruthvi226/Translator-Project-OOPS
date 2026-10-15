import jwt
from sqlalchemy import select
from backend.app.database import User
from tests.conftest import account


def test_health_and_readiness(client):
    assert client.get('/health/live').json()['status'] == 'ok'
    assert client.get('/health/ready').status_code == 200
    assert client.get('/health/ready').json()['provider_connectivity_verified'] is False
    assert client.get('/api/v1/capabilities').json()['providers'][0]['id'] == 'gemini'


def test_auth_hash_login_and_validation(setup, auth):
    client, _, _, factory = setup
    with factory() as db:
        user = db.scalar(select(User))
        assert user.password_hash.startswith('$argon2')
        assert 'strong-password' not in user.password_hash
    assert client.get('/api/v1/me').status_code == 401
    assert client.get('/api/v1/me', headers={'Authorization': 'Bearer invalid'}).status_code == 401
    assert client.get('/api/v1/me', headers=auth).json()['email'] == 'learner@example.com'
    assert client.post('/api/v1/auth/login', json={'email': 'learner@example.com', 'password': 'wrong-password-123'}).status_code == 401
    assert client.post('/api/v1/auth/login', json={'email': 'learner@example.com', 'password': 'strong-password-123'}).status_code == 200
    bad = client.post('/api/v1/auth/signup', json={'email': 'bad', 'password': 'secret'})
    assert bad.status_code == 422 and 'secret' not in bad.text


def test_expired_token_rejected(setup, auth):
    client, _, app, _ = setup
    user_id = client.get('/api/v1/me', headers=auth).json()['id']
    token = jwt.encode({'sub': user_id, 'iat': 1, 'exp': 2, 'iss': 'fluentflow', 'aud': 'fluentflow-api'}, app.state.settings.jwt_secret, algorithm='HS256')
    assert client.get('/api/v1/me', headers={'Authorization': f'Bearer {token}'}).status_code == 401


def test_translation_regression_and_ownership(client, auth):
    result = client.post('/api/v1/translate', json={'text': 'Hello'}, headers=auth)
    assert result.status_code == 200
    assert result.json()['translated_text'] == 'नमस्ते'
    history = client.get('/api/v1/history', headers=auth).json()
    assert len(history) == 1 and history[0]['text'] == 'Hello'
    other = account(client, 'other@example.com')
    assert client.get('/api/v1/history', headers=other).json() == []
    assert client.delete(f"/api/v1/history/{history[0]['id']}", headers=other).status_code == 404
    assert client.post('/api/v1/tutor', json={'session_id': 'test', 'question': 'Explain', 'translation_id': history[0]['id']}, headers=other).status_code == 404
    assert client.get('/api/v1/history?offset=-1', headers=auth).status_code == 422


def test_validation_and_unavailable(setup, auth):
    client, _, app, _ = setup
    for body in [{'text': ''}, {'text': 'a' * 50001}, {'text': 'Hi', 'target_lang': 'invalid'}, {'text': 'Hi', 'tone': 'inject'}]:
        assert client.post('/api/v1/translate', headers=auth, json=body).status_code == 422
    app.state.translator.providers = {}
    result = client.post('/api/v1/translate', headers=auth, json={'text': 'Hello'})
    assert result.status_code == 503 and 'configured' in result.json()['detail']
    assert client.get('/health/ready').status_code == 503
    metrics = client.get('/api/v1/metrics', headers=auth).json()
    assert metrics['failure_rate'] == 1


def test_tutor_memory_and_sources(setup, auth):
    client, provider, _, _ = setup
    body = {'session_id': 'session-1', 'question': 'Explain grammar'}
    first = client.post('/api/v1/tutor', json=body, headers=auth)
    assert first.status_code == 200 and first.json()['sources'] == []
    assert first.json()['source_ids'] == []
    client.post('/api/v1/tutor', json={**body, 'question': 'And pronunciation?'}, headers=auth)
    assert len(provider.calls[-1]['history']) == 1
    other = account(client, 'other@example.com')
    assert client.get('/api/v1/tutor/session-1', headers=other).json() == []
    assert len(client.get('/api/v1/tutor/session-1', headers=auth).json()) == 2
    assert client.get('/api/v1/tutor-sessions', headers=other).json() == []
    sessions = client.get('/api/v1/tutor-sessions', headers=auth).json()
    assert sessions[0]['id'] == 'session-1'


def test_vocabulary_preferences_and_account_deletion(client, auth):
    assert client.post('/api/v1/vocabulary', headers=auth, json={'word': 'नमस्ते', 'meaning': 'Hello', 'language': 'hi'}).status_code == 201
    assert len(client.get('/api/v1/vocabulary', headers=auth).json()) == 1
    assert client.patch('/api/v1/me/preferences', headers=auth, json={'theme': 'dark', 'target_lang': 'kn'}).status_code == 200
    assert client.get('/api/v1/me', headers=auth).json()['preferences']['theme'] == 'dark'
    assert client.delete('/api/v1/me', headers=auth).status_code == 204
    assert client.get('/api/v1/me', headers=auth).status_code == 401


def test_document_job_download_and_isolation(client, auth):
    response = client.post('/api/v1/documents', headers=auth, files={'file': ('notes.txt', b'Hello\n\nWorld', 'text/plain')}, data={'target_lang': 'hi'})
    assert response.status_code == 202, response.text
    job_id = response.json()['id']
    status = client.get(f'/api/v1/documents/{job_id}', headers=auth).json()
    assert status['status'] == 'completed'
    document = client.get(f'/api/v1/documents/{job_id}/download', headers=auth)
    assert document.status_code == 200 and '\n\n' in document.text
    assert client.get(f'/api/v1/documents/{job_id}/download?format=docx', headers=auth).content.startswith(b'PK')
    other = account(client, 'other@example.com')
    assert client.get(f'/api/v1/documents/{job_id}/download', headers=other).status_code == 404


def test_upload_limits_and_invalid_image(client, auth):
    assert client.post('/api/v1/image/translate', headers=auth, files={'file': ('bad.png', b'not-an-image', 'image/png')}).status_code == 422
    assert client.post('/api/v1/documents', headers=auth, files={'file': ('evil.exe', b'MZ', 'application/octet-stream')}).status_code == 415
    assert client.post('/api/v1/documents', headers=auth, files={'file': ('bad.txt', b'x', 'image/png')}).status_code == 415
    response = client.post('/api/v1/translate', headers=auth, content=b'x' * 300001)
    assert response.status_code == 413
    assert client.post('/api/v1/speech/translate', headers=auth, files={'file': ('a.wav', b'RIFF', 'audio/wav')}).status_code == 409
    assert client.post('/api/v1/image/translate', headers=auth, files={'file': ('a.png', b'bad', 'image/png')}, data={'target_lang': 'invalid'}).status_code == 422


def test_mocked_multimodal_pipelines(setup, auth, monkeypatch):
    from backend.app.services import media
    client, _, app, _ = setup
    monkeypatch.setattr(media, 'extract_image', lambda data, language: 'Hello')
    image = client.post('/api/v1/image/translate', headers=auth, files={'file': ('a.png', b'fake-image', 'image/png')})
    assert image.status_code == 200 and image.json()['extracted_text'] == 'Hello'
    app.state.settings.enable_speech = True
    monkeypatch.setattr(media, 'transcribe', lambda *args: {'transcription': 'Hello', 'detected_language': 'en'})
    speech = client.post('/api/v1/speech/translate', headers=auth, files={'file': ('a.wav', b'RIFF', 'audio/wav')})
    assert speech.status_code == 200 and speech.json()['translated_text'] == 'नमस्ते'
    monkeypatch.setattr(media, 'synthesize', lambda *args: b'mp3-bytes')
    audio = client.post('/api/v1/speech/synthesize', headers=auth, json={'text': 'Hello', 'lang': 'en'})
    assert audio.content == b'mp3-bytes' and audio.headers['cache-control'] == 'no-store'


def test_rate_limit(setup):
    client, _, app, _ = setup
    app.state.settings.rate_limit = 2
    assert client.get('/api/v1/capabilities').status_code == 200
    assert client.get('/api/v1/capabilities').status_code == 200
    response = client.get('/api/v1/capabilities')
    assert response.status_code == 429 and response.headers['retry-after'] == '60'


def test_metrics_are_measurements(client, auth):
    assert client.get('/api/v1/metrics', headers=auth).json()['p50_ms'] is None
    client.post('/api/v1/translate', headers=auth, json={'text': 'Hello'})
    metrics = client.get('/api/v1/metrics', headers=auth).json()
    assert metrics['successful'] == 1 and metrics['p50_ms'] >= 0
    assert metrics['quality'] is None and metrics['estimated_cost_usd'] == 0.0001


def test_standalone_static_workspace(setup, tmp_path):
    from fastapi.testclient import TestClient
    from backend.app.config import Settings
    from backend.app.database import get_db
    from backend.app.main import create_app
    _, _, _, factory = setup
    (tmp_path / 'index.html').write_text('<h1>FluentFlow AI</h1>')
    settings = Settings(_env_file=None, gemini_api_key='', frontend_dist=str(tmp_path))
    app = create_app(settings, {}, factory.kw['bind'], factory)
    def db():
        with factory() as session:
            yield session
    app.dependency_overrides[get_db] = db
    with TestClient(app) as browser:
        response = browser.get('/')
        assert response.status_code == 200 and 'FluentFlow AI' in response.text
        assert response.headers['x-frame-options'] == 'DENY'
        assert "frame-ancestors 'none'" in response.headers['content-security-policy']
        assert browser.get('/health/live').status_code == 200
