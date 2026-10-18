import sys

from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.connection import DatabaseNotConfiguredError, create_database_engine


def main() -> int:
    engine = None
    try:
        engine = create_database_engine(Settings())
        with engine.connect() as connection:
            if connection.execute(text("SELECT 1")).scalar_one() != 1:
                raise RuntimeError("Resposta inesperada do PostgreSQL.")
    except DatabaseNotConfiguredError:
        print("Banco não configurado. Preencha DATABASE_URL no backend/.env.", file=sys.stderr)
        return 1
    except (ValidationError, SQLAlchemyError, RuntimeError):
        print(
            "Não foi possível validar a conexão. Confira a configuração local, "
            "as credenciais, o acesso à rede e o SSL.",
            file=sys.stderr,
        )
        return 1
    finally:
        if engine is not None:
            engine.dispose()

    print("Conexão PostgreSQL validada com SELECT 1. Nenhuma tabela foi alterada.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
