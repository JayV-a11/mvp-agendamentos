from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.db.connection import create_database_engine


def get_engine(request: Request):
    # create_app configura o engine sem abrir conexão. Testes injetam um engine local.
    engine = request.app.state.engine
    if engine is None:
        raise HTTPException(503, 'Banco de dados ainda não configurado.')
    return engine


def get_session(request: Request):
    with Session(get_engine(request)) as session, session.begin():
        yield session
