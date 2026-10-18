from pathlib import Path
from urllib.parse import urlsplit

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        env_file_encoding="utf-8",
        extra="forbid",
        hide_input_in_errors=True,
    )

    cors_origins: list[str] = ["http://localhost:4200"]
    database_url: SecretStr | None = None

    @field_validator("database_url", mode="before")
    @classmethod
    def empty_database_url_is_unconfigured(cls, value):
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None:
            return None
        try:
            url = make_url(value.get_secret_value())
            valid = (
                url.drivername == "postgresql+psycopg"
                and bool(url.host and url.database and url.username and url.password)
                and url.query.get("sslmode", "require")
                in {"require", "verify-ca", "verify-full"}
            )
        except (ArgumentError, ValueError):
            valid = False
        if not valid:
            raise ValueError(
                "DATABASE_URL deve usar postgresql+psycopg, conter host, banco, "
                "usuário e senha, e exigir SSL."
            )
        return value

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, origins: list[str]) -> list[str]:
        for origin in origins:
            url = urlsplit(origin)
            if (
                url.scheme not in {"http", "https"}
                or not url.hostname
                or "*" in origin
                or url.username is not None
                or url.password is not None
                or url.path
                or url.query
                or url.fragment
            ):
                raise ValueError("Informe origens HTTP(S) explícitas, sem caminhos ou credenciais.")
            # A leitura da porta também rejeita valores inválidos ou fora do intervalo.
            url.port
        return origins
