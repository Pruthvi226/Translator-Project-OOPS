import asyncio
from datetime import timedelta
from time import perf_counter
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, UploadFile, File, Form
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..config import get_settings
from ..database import Record, User, get_db, now
from ..schemas import Credentials, LANGUAGES, Preferences, SpeechRequest, TranslationRequest, TutorRequest, Vocabulary
from ..security import DUMMY_HASH, current_user, issue_token, passwords
from ..services import media
from ..ai.providers import ProviderUnavailable

router = APIRouter(prefix='/api/v1')


def own_record(db, user, record_id, kind=None):
    record = db.get(Record, record_id)
    if not record or record.user_id != user.id or (kind and record.kind != kind):
        raise HTTPException(404, 'Record not found')
    return record


def save(db, user, kind, data):
    record = Record(user_id=user.id, kind=kind, data=data)
    db.add(record)
    db.commit()
    return record


@router.get('/capabilities')
def capabilities(request: Request):
    settings = request.app.state.settings
    return {'languages': {k: v[0] for k, v in LANGUAGES.items()},
            'providers': [{'id': p.name, 'tone': p.supports_tone} for p in request.app.state.translator.providers.values()],
            'speech': settings.enable_speech, 'rag': settings.enable_rag,
            'upload_limit_mb': settings.max_upload_mb, 'gemini_model': settings.gemini_model}


@router.post('/auth/signup', status_code=201)
def signup(body: Credentials, request: Request, db: Session = Depends(get_db)):
    user = User(email=str(body.email).lower(), name=body.name, password_hash=passwords.hash(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Unable to create account with these details') from None
    return {'access_token': issue_token(user.id, request.app.state.settings), 'token_type': 'bearer'}


@router.post('/auth/login')
def login(body: Credentials, request: Request, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == str(body.email).lower()))
    valid = passwords.verify(body.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid:
        raise HTTPException(401, 'Invalid credentials')
    return {'access_token': issue_token(user.id, request.app.state.settings), 'token_type': 'bearer'}


@router.get('/me')
def profile(user: User = Depends(current_user)):
    return {'id': user.id, 'email': user.email, 'name': user.name, 'preferences': user.preferences}


@router.patch('/me/preferences')
def preferences(body: Preferences, user: User = Depends(current_user), db: Session = Depends(get_db)):
    user.preferences = body.model_dump()
    db.commit()
    return user.preferences


@router.delete('/me', status_code=204)
def delete_account(user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.execute(delete(Record).where(Record.user_id == user.id))
    db.delete(user)
    db.commit()
    return Response(status_code=204)


async def translate_and_save(request, db, user, body):
    started = perf_counter()
    try:
        result = await request.app.state.translator.translate(body)
    except ProviderUnavailable:
        save(db, user, 'usage', {'operation': 'translation', 'failed': True,
                               'latency_ms': (perf_counter() - started) * 1000})
        raise
    record = save(db, user, 'translation', dict(body.model_dump(), **result))
    return dict(result, id=record.id)


@router.post('/translate')
async def translate(body: TranslationRequest, request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return await translate_and_save(request, db, user, body)


@router.get('/history')
def history(user: User = Depends(current_user), db: Session = Depends(get_db), offset: int = 0, limit: int = 30):
    if offset < 0 or not 1 <= limit <= 100:
        raise HTTPException(422, 'Invalid pagination')
    records = db.scalars(select(Record).where(Record.user_id == user.id, Record.kind == 'translation')
                         .order_by(Record.created_at.desc()).offset(offset).limit(limit))
    return [{'id': r.id, 'created_at': r.created_at.isoformat(), **r.data} for r in records]


@router.delete('/history/{record_id}', status_code=204)
def delete_history(record_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(own_record(db, user, record_id, 'translation'))
    db.commit()
    return Response(status_code=204)


@router.get('/vocabulary')
def vocabulary(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return [{'id': r.id, **r.data} for r in db.scalars(select(Record).where(Record.user_id == user.id, Record.kind == 'vocabulary').limit(500))]


@router.post('/vocabulary', status_code=201)
def add_vocabulary(body: Vocabulary, user: User = Depends(current_user), db: Session = Depends(get_db)):
    record = save(db, user, 'vocabulary', body.model_dump())
    return {'id': record.id, **record.data}


@router.delete('/vocabulary/{record_id}', status_code=204)
def remove_vocabulary(record_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    db.delete(own_record(db, user, record_id, 'vocabulary'))
    db.commit()
    return Response(status_code=204)


@router.get('/tutor-sessions')
def tutor_sessions(user: User = Depends(current_user), db: Session = Depends(get_db)):
    records = db.scalars(select(Record).where(Record.user_id == user.id, Record.kind == 'tutor')
                         .order_by(Record.created_at.desc()).limit(1000))
    sessions = {}
    for record in records:
        session_id = record.data['session_id']
        if session_id not in sessions:
            sessions[session_id] = {'id': session_id, 'question': record.data['question'],
                                    'updated_at': record.created_at.isoformat()}
    return list(sessions.values())[:30]


@router.get('/tutor/{session_id}')
def tutor_history(session_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    turns = db.scalars(select(Record).where(Record.user_id == user.id, Record.kind == 'tutor',
                       Record.data['session_id'].as_string() == session_id)
                       .order_by(Record.created_at.desc()).limit(100))
    return [r.data for r in reversed(list(turns)) if r.data.get('session_id') == session_id]


@router.post('/tutor')
async def tutor(body: TutorRequest, request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    provider = request.app.state.translator.providers.get('gemini')
    if not provider:
        raise ProviderUnavailable('Tutor requires a configured Gemini provider')
    context = own_record(db, user, body.translation_id, 'translation').data if body.translation_id else {}
    turns = db.scalars(select(Record).where(Record.user_id == user.id, Record.kind == 'tutor',
                       Record.data['session_id'].as_string() == body.session_id)
                       .order_by(Record.created_at.desc()).limit(100))
    history = [r.data for r in reversed(list(turns)) if r.data.get('session_id') == body.session_id][-6:]
    sources = []
    if body.use_rag:
        if not request.app.state.settings.enable_rag:
            raise HTTPException(409, 'RAG is disabled')
        try:
            sources = await asyncio.to_thread(request.app.state.knowledge.retrieve, body.question)
        except Exception:
            raise ProviderUnavailable('Knowledge retrieval unavailable; verify optional models and dependencies') from None
    try:
        async with request.app.state.media_gate:
            result = await asyncio.wait_for(provider.tutor({'question': body.question, 'translation': context,
                                        'history': history, 'sources': sources}), request.app.state.settings.provider_timeout)
    except Exception:
        raise ProviderUnavailable('Tutor temporarily unavailable') from None
    valid_ids = set(result.source_ids)
    result.source_ids = [s['id'] for s in sources if s['id'] in valid_ids]
    response = dict(result.model_dump(), sources=[s for s in sources if s['id'] in result.source_ids])
    save(db, user, 'tutor', {'session_id': body.session_id, 'question': body.question, **response})
    return response


@router.post('/speech/synthesize')
async def speech_synthesize(body: SpeechRequest, request: Request, user: User = Depends(current_user)):
    try:
        async with request.app.state.media_gate:
            result = await asyncio.to_thread(media.synthesize, body.text, body.lang)
    except HTTPException:
        raise
    except Exception:
        raise ProviderUnavailable('Speech synthesis temporarily unavailable') from None
    return Response(result, media_type='audio/mpeg', headers={'Cache-Control': 'no-store'})


@router.post('/speech/translate')
async def speech_translate(request: Request, file: UploadFile = File(...), target_lang: str = Form('hi'),
                           user: User = Depends(current_user), db: Session = Depends(get_db)):
    if not request.app.state.settings.enable_speech:
        await file.close()
        raise HTTPException(409, 'Server speech recognition is disabled; enable it and install faster-whisper')
    body = TranslationRequest(text='validation', target_lang=target_lang)
    data, suffix = await media.read_upload(file, media.AUDIO_TYPES, request.app.state.settings.max_upload_mb * 1024**2)
    async with request.app.state.media_gate:
        transcription = await asyncio.to_thread(media.transcribe, data, suffix, request.app.state.settings.whisper_model)
    body.text = transcription['transcription']
    detected = transcription['detected_language']
    body.src_lang = detected if detected in LANGUAGES else 'auto'
    result = await translate_and_save(request, db, user, body)
    return dict(result, transcription=transcription['transcription'])


@router.post('/image/translate')
async def image_translate(request: Request, file: UploadFile = File(...), target_lang: str = Form('hi'),
                          ocr_language: str = Form('eng'), user: User = Depends(current_user), db: Session = Depends(get_db)):
    if ocr_language not in {'eng', 'hin', 'kan', 'tam', 'tel', 'mal', 'mar', 'ben', 'guj', 'pan', 'urd', 'fra', 'deu', 'spa', 'jpn', 'kor', 'chi_sim', 'ara'}:
        await file.close()
        raise HTTPException(422, 'Unsupported OCR language pack')
    body = TranslationRequest(text='validation', target_lang=target_lang)
    data, _ = await media.read_upload(file, media.IMAGE_TYPES, request.app.state.settings.max_upload_mb * 1024**2)
    async with request.app.state.media_gate:
        text = await asyncio.to_thread(media.extract_image, data, ocr_language)
    body = body.model_copy(update={'text': text})
    if len(text) > 50000:
        raise HTTPException(422, 'OCR output exceeds text limit')
    result = await translate_and_save(request, db, user, body)
    return dict(result, extracted_text=text)


async def run_document(app, record_id, data, suffix, options):
    # A session belongs to this job only; uploads live in memory and are discarded.
    with app.state.session_factory() as db:
        record = db.get(Record, record_id)
        if not record:
            return
        record.data = {'status': 'running'}
        db.commit()
        try:
            async with app.state.media_gate:
                text = await asyncio.to_thread(media.extract_document, data, suffix)
            result = await app.state.translator.translate(options.model_copy(update={'text': text}))
            db.refresh(record)
            record.data = {'status': 'completed', **result}
            db.commit()
        except Exception:
            db.rollback()
            record = db.get(Record, record_id)
            if record:
                record.data = {'status': 'failed', 'error': 'Document processing failed; verify format and provider configuration'}
                db.commit()


@router.post('/documents', status_code=202)
async def document_upload(request: Request, background: BackgroundTasks, file: UploadFile = File(...),
                          target_lang: str = Form('hi'), user: User = Depends(current_user), db: Session = Depends(get_db)):
    body = TranslationRequest(text='validation', target_lang=target_lang)
    data, suffix = await media.read_upload(file, media.DOC_TYPES, request.app.state.settings.max_upload_mb * 1024**2)
    record = save(db, user, 'job', {'status': 'queued'})
    background.add_task(run_document, request.app, record.id, data, suffix, body)
    return {'id': record.id, 'status': 'queued'}


@router.get('/documents/{job_id}')
def document_status(job_id: str, user: User = Depends(current_user), db: Session = Depends(get_db)):
    record = own_record(db, user, job_id, 'job')
    return {'id': record.id, **record.data}


@router.get('/documents/{job_id}/download')
def document_download(job_id: str, format: str = 'txt', user: User = Depends(current_user), db: Session = Depends(get_db)):
    record = own_record(db, user, job_id, 'job')
    if record.data.get('status') != 'completed':
        raise HTTPException(409, 'Document is not ready')
    text = record.data['translated_text']
    if format == 'txt':
        content, content_type = text.encode('utf-8'), 'text/plain; charset=utf-8'
    elif format == 'docx':
        content, content_type = media.export_docx(text), media.DOC_TYPES['.docx']
    else:
        raise HTTPException(422, 'Choose txt or docx')
    return Response(content, media_type=content_type, headers={
        'Content-Disposition': f'attachment; filename="fluentflow-translation.{format}"', 'Cache-Control': 'no-store'})


@router.get('/metrics')
def metrics(user: User = Depends(current_user), db: Session = Depends(get_db)):
    import numpy as np
    records = list(db.scalars(select(Record).where(Record.user_id == user.id,
                        Record.kind.in_(['translation', 'usage'])).order_by(Record.created_at.desc()).limit(1000)))
    successful = [r.data for r in records if r.kind == 'translation']
    latencies = [r.data['latency_ms'] for r in records if 'latency_ms' in r.data]
    costs = [d['estimated_cost_usd'] for d in successful if d.get('estimated_cost_usd') is not None]
    return {'requests': len(records), 'sample_limit': 1000, 'successful': len(successful),
            'failure_rate': sum(r.data.get('failed', False) for r in records) / len(records) if records else None,
            'fallback_rate': sum(d.get('fallback', False) for d in successful) / len(successful) if successful else None,
            'p50_ms': float(np.percentile(latencies, 50)) if latencies else None,
            'p95_ms': float(np.percentile(latencies, 95)) if latencies else None,
            'estimated_cost_usd': sum(costs) if costs else None,
            'quality': None, 'quality_note': 'Run the offline evaluation CLI with reference translations; quality is not inferred from usage.'}


@router.post('/me/purge-expired')
def purge(user: User = Depends(current_user), db: Session = Depends(get_db)):
    result = db.execute(delete(Record).where(Record.user_id == user.id,
                         Record.created_at < now() - timedelta(days=get_settings().retention_days)))
    db.commit()
    return {'deleted': result.rowcount}
