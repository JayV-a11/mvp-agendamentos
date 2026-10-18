from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.api.health import router as health_router
from app.core.config import Settings
from app.core.http import RequestLimitsMiddleware
from app.db.connection import create_database_engine
from app.api import auth, catalogo, agenda, photos


def create_app(settings: Settings | None = None, *, engine=None) -> FastAPI:
    settings = settings if settings is not None else Settings()
    owned_engine = engine is None and settings.database_url is not None
    if owned_engine:
        engine = create_database_engine(settings)

    @asynccontextmanager
    async def lifespan(app):
        yield
        if owned_engine:
            engine.dispose()

    application = FastAPI(title="API de Agendamentos", debug=False, lifespan=lifespan)
    application.state.settings = settings
    application.state.engine = engine
    application.add_middleware(RequestLimitsMiddleware, production=settings.environment == 'production')
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=['Content-Type', 'X-CSRF-Token'],
    )
    application.include_router(health_router)
    for router in (auth.router, catalogo.public, catalogo.admin, agenda.public, agenda.admin, photos.router):
        application.include_router(router)

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error):
        # Pydantic inclui input/ctx nas falhas: não refletir senha, telefone ou tokens.
        fields = [{'loc': list(item['loc']), 'type': item['type'],
            'msg': 'Valor inválido ou campo obrigatório ausente.'} for item in error.errors()]
        return JSONResponse({'detail': fields}, status_code=422)

    @application.exception_handler(IntegrityError)
    async def conflict(request: Request, error):
        return JSONResponse({'detail': 'Operação em conflito com os dados atuais. Atualize e tente novamente.'}, 409)

    @application.exception_handler(SQLAlchemyError)
    async def database_error(request: Request, error):
        if getattr(getattr(error, 'orig', None), 'sqlstate', None) in {'40P01', '40001', '55P03'}:
            return JSONResponse({'detail': 'Operação concorrente em conflito. Atualize e tente novamente.'}, 409)
        return JSONResponse({'detail': 'Não foi possível concluir a operação. Tente novamente mais tarde.'}, 503)
    return application
