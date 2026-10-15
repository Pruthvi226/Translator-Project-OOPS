from datetime import timedelta
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from sqlalchemy.orm import Session
from .config import get_settings
from .database import User, get_db, now

passwords = PasswordHash.recommended()
DUMMY_HASH = passwords.hash('dummy-password-for-timing-only')
bearer = HTTPBearer(auto_error=False)


def issue_token(user_id, settings=None):
    settings = settings or get_settings()
    return jwt.encode({'sub': user_id, 'iat': now(),
                       'exp': now() + timedelta(minutes=settings.token_minutes),
                       'iss': 'fluentflow', 'aud': 'fluentflow-api'},
                      settings.jwt_secret, algorithm='HS256')


def current_user(request: Request, auth: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)):
    try:
        if not auth:
            raise ValueError('Missing token')
        payload = jwt.decode(auth.credentials, request.app.state.settings.jwt_secret,
                             algorithms=['HS256'], issuer='fluentflow', audience='fluentflow-api',
                             options={'require': ['exp', 'iat', 'sub']})
        user = db.get(User, payload['sub'])
        if not user:
            raise ValueError('Unknown user')
        return user
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(401, 'Authentication required', headers={'WWW-Authenticate': 'Bearer'}) from None
