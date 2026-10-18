from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.pool import NullPool

from app.core.config import Settings


class DatabaseNotConfiguredError(RuntimeError):
    pass


def create_database_engine(settings: Settings) -> Engine:
    if settings.database_url is None:
        raise DatabaseNotConfiguredError("Preencha DATABASE_URL no backend/.env local.")

    url = make_url(settings.database_url.get_secret_value())
    return create_engine(
        url,
        connect_args={
            "sslmode": url.query.get("sslmode", "require"),
            "connect_timeout": 10,
        },
        poolclass=NullPool,
        echo=False,
        hide_parameters=True,
    )
