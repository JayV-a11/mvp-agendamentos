from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, Header
from fastapi.security import APIKeyCookie
from sqlalchemy.orm import Session

from app.core.security import COOKIE, decode_token, check_csrf, now
from app.db.session import get_session
from app.models import Administrador
from app.models.auth import SessaoAdministrativa

DB = Annotated[Session, Depends(get_session, scope='function')]
cookie = APIKeyCookie(name=COOKIE, auto_error=False)


@dataclass
class Identity:
    admin: Administrador
    session: SessaoAdministrativa


def authenticated(request: Request, db: DB, token: Annotated[str | None, Depends(cookie)],
    csrf_header: Annotated[str | None, Header(alias='X-CSRF-Token',
        description='Token retornado pelo login/sessão; obrigatório nas mutações autenticadas.')] = None):
    if not token:
        raise HTTPException(401, 'Autenticação necessária.')
    admin_id, session_id = decode_token(request.app.state.settings, token)
    record = db.get(SessaoAdministrativa, session_id)
    admin = db.get(Administrador, admin_id)
    if record is None or record.administrador_id != admin_id or record.expira_em <= now() or admin is None:
        raise HTTPException(401, 'Sessão inválida ou expirada.')
    if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
        check_csrf(request, session_id)
    return Identity(admin, record)


Auth = Annotated[Identity, Depends(authenticated, scope='function')]
