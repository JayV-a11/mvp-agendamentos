from alembic import context
from alembic.util import CommandError
from pydantic import ValidationError
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import Settings
from app.db.base import Base
from app.db.connection import DatabaseNotConfiguredError, create_database_engine
from app import models  # Registra os modelos no metadata usado pelo Alembic.

target_metadata = Base.metadata


def include_name(name, type_, parent_names):
    # Autogenerate deve inspecionar somente tabelas deste MVP, sem sugerir
    # exclusões de objetos externos que compartilhem o banco do Supabase.
    if type_ == "table":
        return name in target_metadata.tables
    return True


def run_migrations() -> None:
    engine = None
    try:
        provided_connection = context.config.attributes.get("connection")
        if provided_connection is not None and not context.is_offline_mode():
            context.configure(
                connection=provided_connection,
                target_metadata=target_metadata,
                compare_type=True,
                include_name=include_name,
            )
            with context.begin_transaction():
                context.run_migrations()
            return

        settings = Settings()
        if settings.database_url is None:
            raise DatabaseNotConfiguredError()

        if context.is_offline_mode():
            context.configure(
                url=make_url(settings.database_url.get_secret_value()),
                target_metadata=target_metadata,
                literal_binds=True,
                dialect_opts={"paramstyle": "named"},
                include_name=include_name,
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
                    include_name=include_name,
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
