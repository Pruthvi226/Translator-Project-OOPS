import asyncio
from collections import OrderedDict, deque
from contextlib import asynccontextmanager
from datetime import timedelta
import json
import logging
import jwt
from time import monotonic, perf_counter
from uuid import uuid4
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from sqlalchemy import delete, select, text
from .ai.providers import ProviderUnavailable, build_providers
from .config import get_settings
from .database import Base, Record, SessionLocal, engine, now
from .routes.api import router
from .services.rag import KnowledgeBase
from .services.translation import TranslationService


class JsonFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({'level': record.levelname, 'event': record.getMessage(),
                           **{key: getattr(record, key) for key in ('request_id', 'status', 'latency_ms', 'provider', 'error_type') if hasattr(record, key)}})


handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
logger = logging.getLogger('fluentflow')
logger.handlers = [handler]
logger.setLevel(logging.INFO)
logger.propagate = False


def create_app(settings=None, providers=None, db_engine=None, session_factory=None):
    settings = settings or get_settings()
    selected_engine = db_engine or engine
    factory = session_factory or SessionLocal

    @asynccontextmanager
    async def lifespan(app):
        Base.metadata.create_all(selected_engine)
        with factory() as db:
            # A single instance owns background jobs. Interrupted jobs are explicit failures.
            for record in db.scalars(select(Record).where(Record.kind == 'job')):
                if record.data.get('status') in {'queued', 'running'}:
                    record.data = {'status': 'failed', 'error': 'Processing interrupted; upload again'}
            db.execute(delete(Record).where(Record.created_at < now() - timedelta(days=settings.retention_days)))
            db.commit()
        async def retention():
            while True:
                await asyncio.sleep(3600)
                with factory() as db:
                    db.execute(delete(Record).where(Record.created_at < now() - timedelta(days=settings.retention_days)))
                    db.commit()
        task = asyncio.create_task(retention())
        yield
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        for provider in app.state.translator.providers.values():
            if hasattr(provider, 'client'):
                await provider.client.aio.aclose()
                provider.client.close()

    app = FastAPI(title='FluentFlow AI', version='1.0.0', lifespan=lifespan)
    app.state.settings = settings
    app.state.session_factory = factory
    app.state.translator = TranslationService(settings, providers if providers is not None else build_providers(settings))
    app.state.knowledge = KnowledgeBase()
    app.state.media_gate = asyncio.Semaphore(2)
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins.split(','),
                       allow_methods=['GET', 'POST', 'PATCH', 'DELETE'], allow_headers=['Authorization', 'Content-Type'])
    buckets = OrderedDict()

    @app.middleware('http')
    async def protect(request: Request, call_next):
        request_id = uuid4().hex
        started = perf_counter()
        if request.url.path.startswith('/api/'):
            # Do not trust forwarded headers. Apply distributed limits at the ingress for replicas.
            key = request.client.host if request.client else 'unknown'
            authorization = request.headers.get('authorization', '')
            if authorization.startswith('Bearer '):
                try:
                    claims = jwt.decode(authorization[7:], settings.jwt_secret, algorithms=['HS256'],
                                        issuer='fluentflow', audience='fluentflow-api',
                                        options={'require': ['sub', 'iat', 'exp']})
                    key = 'user:' + claims['sub']
                except (jwt.InvalidTokenError, TypeError, KeyError):
                    pass
            stamp = monotonic()
            bucket = buckets.setdefault(key, deque())
            buckets.move_to_end(key)
            while bucket and stamp - bucket[0] > 60:
                bucket.popleft()
            if len(bucket) >= settings.rate_limit:
                return JSONResponse({'detail': 'Request limit reached', 'request_id': request_id}, 429,
                                    headers={'Retry-After': '60'})
            bucket.append(stamp)
            while len(buckets) > 10000:
                buckets.popitem(last=False)
        limit = (settings.max_upload_mb + 1) * 1024**2 if 'multipart/form-data' in request.headers.get('content-type', '') else 300000
        try:
            if int(request.headers.get('content-length', '0')) > limit:
                return JSONResponse({'detail': 'Request too large'}, 413)
        except ValueError:
            return JSONResponse({'detail': 'Invalid content length'}, 400)
        # Enforce a streaming limit as well, including chunked requests.
        received = 0
        original_receive = request._receive
        async def receive():
            nonlocal received
            message = await original_receive()
            received += len(message.get('body', b''))
            if received > limit:
                raise HTTPException(413, 'Request too large')
            return message
        request._receive = receive
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error('request_failed', extra={'request_id': request_id, 'error_type': type(exc).__name__})
            response = JSONResponse({'detail': 'Request could not be completed', 'request_id': request_id}, 500)
        response.headers.update({'X-Request-ID': request_id, 'X-Content-Type-Options': 'nosniff',
                                 'Referrer-Policy': 'same-origin', 'Cache-Control': 'no-store',
                                 'X-Frame-Options': 'DENY'})
        if settings.frontend_dist and request.url.path not in {'/docs', '/redoc'}:
            response.headers['Content-Security-Policy'] = (
                "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src 'self' https://fonts.gstatic.com; img-src 'self' blob: data:; media-src 'self' blob:; "
                "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'")
        logger.info('request_completed', extra={'request_id': request_id, 'status': response.status_code,
                                                'latency_ms': round((perf_counter() - started) * 1000, 2)})
        return response

    @app.exception_handler(RequestValidationError)
    @app.exception_handler(ValidationError)
    async def validation_error(request, exc):
        # Pydantic's default errors echo input values, which can include passwords.
        return JSONResponse({'detail': [{'loc': list(e['loc']), 'msg': e['msg'], 'type': e['type']} for e in exc.errors()]}, 422)

    @app.exception_handler(ProviderUnavailable)
    async def provider_error(request, exc):
        return JSONResponse({'detail': str(exc)}, 503)

    @app.get('/health/live')
    def live():
        return {'status': 'ok'}

    @app.get('/health/ready')
    def ready():
        try:
            with selected_engine.connect() as connection:
                connection.execute(text('SELECT 1'))
        except Exception:
            return JSONResponse({'status': 'not_ready', 'database': False}, 503)
        configured = bool(app.state.translator.providers)
        return JSONResponse({'status': 'ready' if configured else 'not_ready', 'database': True,
                             'provider_configured': configured, 'provider_connectivity_verified': False}, 200 if configured else 503)

    app.include_router(router)
    if settings.frontend_dist:
        app.mount('/', StaticFiles(directory=settings.frontend_dist, html=True), name='workspace')
    return app


app = create_app()
