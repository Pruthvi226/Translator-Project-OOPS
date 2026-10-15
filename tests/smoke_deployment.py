"""Explicit live-HTTP smoke test for an isolated, empty deployment.

Run only against deployment/compose.verify.yml. Creates/deletes temporary accounts.
No external providers or paid APIs are called.
"""
import os
from uuid import uuid4
import httpx


def main():
    base = os.getenv('SMOKE_BASE_URL', 'http://127.0.0.1:18080')
    with httpx.Client(base_url=base, timeout=20) as client:
        root = client.get('/')
        assert root.status_code == 200 and 'FluentFlow' in root.text
        assert client.get('/health/live').status_code == 200
        ready = client.get('/health/ready')
        assert ready.status_code == 503 and ready.json()['database'] is True
        assert ready.json()['provider_configured'] is False
        accounts = []
        for _ in range(2):
            email = f'smoke-{uuid4().hex}@example.com'
            response = client.post('/api/v1/auth/signup', json={'email': email, 'password': 'smoke-test-password-123'})
            assert response.status_code == 201, response.text
            accounts.append({'Authorization': f"Bearer {response.json()['access_token']}"})
        first, second = accounts
        assert client.get('/api/v1/me').status_code == 401
        saved = client.post('/api/v1/vocabulary', headers=first,
                            json={'word': 'नमस्ते', 'meaning': 'Hello', 'language': 'hi'})
        assert saved.status_code == 201
        assert len(client.get('/api/v1/vocabulary', headers=first).json()) == 1
        assert client.get('/api/v1/vocabulary', headers=second).json() == []
        assert client.delete('/api/v1/vocabulary/' + saved.json()['id'], headers=second).status_code == 404
        unavailable = client.post('/api/v1/translate', headers=first, json={'text': 'Hello'})
        assert unavailable.status_code == 503
        assert client.get('/api/v1/metrics', headers=first).json()['failure_rate'] == 1
        for auth in accounts:
            assert client.delete('/api/v1/me', headers=auth).status_code == 204
    print('Live Nginx + FastAPI + PostgreSQL smoke test passed; no provider calls made.')


if __name__ == '__main__':
    main()
