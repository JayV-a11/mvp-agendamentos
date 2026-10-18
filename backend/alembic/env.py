from alembic import context
from alembic.util import CommandError
from pydantic import ValidationError
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.base import Base
from app.db.connection import DatabaseNotConfiguredError, create_database_engine

target_metadata = Base.metadata


def run_migrations() -> None:
    engine = None
    try:
        settings = Settings()
        if settings.database_url is None:
            raise DatabaseNotConfiguredError()

        if context.is_offline_mode():
            context.configure(
                url=make_url(settings.database_url.get_secret_value()),
                target_metadata=target_metadata,
                literal_binds=True,
                dialect_opts={"paramstyle": "named"},
            )
            with context.begin_transaction():
                context.run_migrations()
        else:
            engine = create_database_engine(settings)
            with engine.connect() as connection:
                context.configure(
                    connection=connection,
                    target_metadata=target_metadata,
                    compare_type=True,
                )
                with context.begin_transaction():
                    context.run_migrations()
    except DatabaseNotConfiguredError:
        raise CommandError("Preencha DATABASE_URL no backend/.env local.") from None
    except (ValidationError, SQLAlchemyError):
        raise CommandError(
            "Falha na configuração ou conexão do Alembic. "
            "Confira o .env, o acesso à rede e o SSL."
        ) from None
    finally:
        if engine is not None:
            engine.dispose()


run_migrations()
