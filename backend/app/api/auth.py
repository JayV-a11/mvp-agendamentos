from fastapi import APIRouter, Request, Response

from app.api.dependencies import DB, Auth
from app.core.security import COOKIE, SESSION_SECONDS, csrf_token, check_origin
from app.db.session import get_engine
from app.schemas.domain import Login, SessionOutput
from app.services.auth import limit_requests, login

router = APIRouter(prefix='/auth', tags=['Autenticação'])


def output(settings, admin, session):
    return SessionOutput(nome=admin.nome, csrf_token=csrf_token(settings, session.id), expira_em=session.expira_em)


@router.post('/login', response_model=SessionOutput)
def sign_in(data: Login, request: Request, response: Response, db: DB):
    check_origin(request)
    settings = request.app.state.settings
    ip = request.client.host if request.client else 'desconhecido'
    engine = get_engine(request)
    limit_requests(engine, settings, 'login-ip', ip, 30, 900)
    limit_requests(engine, settings, 'login-conta', data.email, 5, 900)
    admin, session, token = login(db, settings, data.email, data.senha)
    response.set_cookie(COOKIE, token, max_age=SESSION_SECONDS, httponly=True,
        secure=settings.cookie_secure, samesite=settings.cookie_samesite, path='/')
    response.headers['Cache-Control'] = 'no-store'
    return output(settings, admin, session)


@router.get('/sessao', response_model=SessionOutput)
def session_info(request: Request, response: Response, identity: Auth):
    response.headers['Cache-Control'] = 'no-store'
    return output(request.app.state.settings, identity.admin, identity.session)


@router.post('/logout', status_code=204)
def sign_out(request: Request, response: Response, db: DB, identity: Auth):
    db.delete(identity.session)
    db.flush()
    settings = request.app.state.settings
    response.delete_cookie(COOKIE, path='/', secure=settings.cookie_secure,
        httponly=True, samesite=settings.cookie_samesite)
    response.headers['Cache-Control'] = 'no-store'
