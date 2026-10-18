from pathlib import Path
from urllib.parse import urlsplit

from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import SecretStr, field_validator, model_validator
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
    jwt_secret: SecretStr | None = None
    environment: Literal['development', 'production'] = 'development'
    cookie_secure: bool = False
    cookie_samesite: Literal['lax', 'strict', 'none'] = 'lax'
    business_timezone: str = 'America/Sao_Paulo'
    supabase_url: str | None = None
    supabase_service_key: SecretStr | None = None
    storage_bucket: str = 'fotos-servicos'

    @field_validator('jwt_secret', 'supabase_service_key', 'supabase_url', mode='before')
    @classmethod
    def empty_optional(cls, value):
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator('jwt_secret')
    @classmethod
    def strong_secret(cls, value):
        if value is not None and len(value.get_secret_value().encode()) < 32:
            raise ValueError('JWT_SECRET deve conter pelo menos 32 bytes aleatórios.')
        return value

    @field_validator('business_timezone')
    @classmethod
    def valid_timezone(cls, value):
        try:
            ZoneInfo(value)
        except ZoneInfoNotFoundError:
            raise ValueError('Fuso IANA inválido.') from None
        return value

    @field_validator('supabase_url')
    @classmethod
    def valid_storage_url(cls, value):
        if value is None:
            return value
        url = urlsplit(value)
        if (url.scheme != 'https' or not url.hostname or url.username or url.password
                or url.path not in {'', '/'} or url.query or url.fragment):
            raise ValueError('SUPABASE_URL deve ser a origem HTTPS do projeto.')
        url.port
        return value.rstrip('/')

    @field_validator('storage_bucket')
    @classmethod
    def valid_bucket(cls, value):
        import re
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,62}', value):
            raise ValueError('Nome de bucket inválido.')
        return value

    @model_validator(mode='after')
    def production_security(self):
        if self.cookie_samesite == 'none' and not self.cookie_secure:
            raise ValueError('SameSite=None exige cookie Secure.')
        if self.environment == 'production' and (
            not self.cookie_secure or self.jwt_secret is None or self.database_url is None
            or not self.cors_origins or any(not o.startswith('https://') for o in self.cors_origins)
        ):
            raise ValueError('Produção exige banco, segredo JWT, cookie Secure e origens HTTPS.')
        return self

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
