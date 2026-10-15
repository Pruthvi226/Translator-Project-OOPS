import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from backend.app.config import Settings
from backend.app.database import get_db, make_engine
from backend.app.main import create_app
from backend.app.ai.providers import Completion
from backend.app.schemas import TranslationOutput, TutorOutput


class MockProvider:
    name = 'gemini'
    supports_tone = True

    def __init__(self):
        self.calls = []

    async def translate(self, text, src, target, tone):
        self.calls.append((text, src, target, tone))
        return Completion(TranslationOutput(translated_text={'Hello': 'नमस्ते'}.get(text, f'[{target}] {text}'), detected_language='en'), 10, 8, 0.0001)

    async def tutor(self, payload):
        self.calls.append(payload)
        return TutorOutput(answer='This is a polite greeting.', source_ids=['invented-source'])


@pytest.fixture
def setup(tmp_path):
    settings = Settings(_env_file=None, jwt_secret='test-secret-that-is-longer-than-32-characters',
                        rate_limit=500, provider_timeout=1, provider_retries=0, gemini_api_key='')
    engine = make_engine('sqlite:///' + str(tmp_path / 'test.db'))
    factory = sessionmaker(engine, expire_on_commit=False)
    provider = MockProvider()
    app = create_app(settings, {'gemini': provider}, engine, factory)
    def override_db():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = override_db
    with TestClient(app) as client:
        yield client, provider, app, factory
    engine.dispose()


@pytest.fixture
def client(setup):
    return setup[0]


def account(client, email='learner@example.com'):
    response = client.post('/api/v1/auth/signup', json={'email': email, 'password': 'strong-password-123', 'name': 'Learner'})
    assert response.status_code == 201, response.text
    return {'Authorization': f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def auth(client):
    return account(client)
