import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
from fastapi import HTTPException, Request
from pwdlib import PasswordHash

COOKIE = 'agendamento_sessao'
SESSION_SECONDS = 1800
PASSWORDS = PasswordHash.recommended()
# Evita retorno antecipado quando o e-mail não existe.
DUMMY_HASH = PASSWORDS.hash('credencial-inutilizada-' + str(uuid4()))


def now():
    return datetime.now(timezone.utc)


def secret(settings):
    if settings.jwt_secret is None:
        raise HTTPException(503, 'Autenticação ainda não configurada.')
    return settings.jwt_secret.get_secret_value()


def csrf_token(settings, session_id):
    return hmac.new(secret(settings).encode(), f'csrf:{session_id}'.encode(), hashlib.sha256).hexdigest()


def issue_token(settings, admin_id, session_id, expires):
    return jwt.encode({'sub': str(admin_id), 'jti': str(session_id),
        'iat': now(), 'exp': expires, 'iss': 'agendamentos', 'aud': 'administracao'},
        secret(settings), algorithm='HS256')


def decode_token(settings, token):
    try:
        claims = jwt.decode(token, secret(settings), algorithms=['HS256'],
            issuer='agendamentos', audience='administracao',
            options={'require': ['sub', 'jti', 'iat', 'exp', 'iss', 'aud']})
        return UUID(claims['sub']), UUID(claims['jti'])
    except (jwt.PyJWTError, ValueError, TypeError, KeyError):
        raise HTTPException(401, 'Sessão inválida ou expirada.') from None


def check_origin(request: Request):
    origin = request.headers.get('origin')
    allowed = request.app.state.settings.cors_origins
    own = str(request.base_url).rstrip('/')
    if origin is not None and origin not in [*allowed, own]:
        raise HTTPException(403, 'Origem não autorizada.')


def check_csrf(request, session_id):
    check_origin(request)
    token = request.headers.get('x-csrf-token', '')
    if not hmac.compare_digest(token, csrf_token(request.app.state.settings, session_id)):
        raise HTTPException(403, 'Proteção CSRF: atualize a sessão e tente novamente.')
