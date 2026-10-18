import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_carrega_origens_da_variavel_de_ambiente(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", '["https://frontend.example"]')

    settings = Settings(_env_file=None)

    assert settings.cors_origins == ["https://frontend.example"]


@pytest.mark.parametrize(
    "origin",
    [
        "*",
        "http://*.example",
        "http://localhost:4200/rota",
        "http://localhost:4200/",
        "http://usuario:senha@localhost:4200",
        "ftp://localhost",
        "http://localhost:99999",
    ],
)
def test_rejeita_origem_invalida(origin):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, cors_origins=[origin])
