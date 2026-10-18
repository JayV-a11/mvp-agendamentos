"""Inicialização local sem senha em argumentos, histórico do terminal ou fonte."""
import argparse
import getpass
import secrets
from pathlib import Path

from dotenv import dotenv_values, set_key
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.connection import create_database_engine, DatabaseNotConfiguredError
from app.schemas.domain import AdminCreate
from app.services.auth import create_first_admin


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['segredo', 'administradora'])
    action = parser.parse_args().action
    if action == 'segredo':
        path = Path(__file__).resolve().parents[2] / '.env'
        if not path.exists():
            print('Crie backend/.env a partir de .env.example primeiro.')
            return 1
        if dotenv_values(path).get('JWT_SECRET'):
            print('JWT_SECRET já está configurado; nenhuma alteração realizada.')
        else:
            set_key(str(path), 'JWT_SECRET', secrets.token_urlsafe(48))
            print('JWT_SECRET gerado no arquivo local, sem exibição do valor.')
        return 0
    engine = None
    try:
        data = AdminCreate(nome=input('Nome da administradora: '), email=input('E-mail: '))
        password = getpass.getpass('Senha (12 a 128 caracteres): ')
        if password != getpass.getpass('Confirme a senha: '):
            print('As senhas não coincidem.')
            return 1
        settings = Settings()
        engine = create_database_engine(settings)
        with Session(engine) as session, session.begin():
            create_first_admin(session, data.nome, data.email, password)
        print('Administradora criada. Nenhuma senha ou token foi exibido.')
        return 0
    except (ValidationError, ValueError):
        print('Dados inválidos ou administradora já existente. Confira nome, e-mail e tamanho da senha.')
        return 1
    except (SQLAlchemyError, DatabaseNotConfiguredError):
        print('Falha no banco. Confira a configuração e aplique as migrações.')
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == '__main__':
    raise SystemExit(main())
