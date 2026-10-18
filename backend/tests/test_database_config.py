import os
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError
from sqlalchemy.pool import NullPool

from app.core.config import Settings
from app.db.connection import DatabaseNotConfiguredError, create_database_engine

# Credenciais sintéticas usadas somente na construção da configuração, sem conexão.
TEST_URL = "postgresql+psycopg://usuario:senha_de_teste@localhost:5432/testes"


def test_url_vazia_mantem_banco_sem_configuracao():
    settings = Settings(_env_file=None, database_url="")

    with pytest.raises(DatabaseNotConfiguredError):
        create_database_engine(settings)


def test_url_e_senha_nao_aparecem_na_representacao_da_configuracao():
    settings = Settings(_env_file=None, database_url=TEST_URL)

    for representation in (str(settings), repr(settings), settings.model_dump_json()):
        assert TEST_URL not in representation
        assert "senha_de_teste" not in representation


@pytest.mark.parametrize(
    "url",
    [
        "sqlite:///testes.db",
        "postgresql://usuario:senha_de_teste@localhost/testes",
        "postgresql+psycopg://usuario@localhost/testes",
        TEST_URL + "?sslmode=disable",
        "postgresql+psycopg://usuario:senha_de_teste@localhost:porta/testes",
    ],
)
def test_rejeita_conexao_invalida_sem_expor_senha(url):
    with pytest.raises(ValidationError) as error:
        Settings(_env_file=None, database_url=url)

    assert "senha_de_teste" not in str(error.value)
    assert url not in str(error.value)


def test_engine_carrega_driver_postgresql_sem_abrir_conexao():
    engine = create_database_engine(Settings(_env_file=None, database_url=TEST_URL))
    try:
        assert engine.dialect.name == "postgresql"
        assert engine.dialect.driver == "psycopg"
        assert isinstance(engine.pool, NullPool)
        assert engine.hide_parameters is True
        assert engine.echo is False
    finally:
        engine.dispose()


def test_comando_sem_configuracao_informa_pendencia_sem_traceback():
    env = os.environ.copy()
    env["DATABASE_URL"] = ""
    env["CORS_ORIGINS"] = '["http://localhost:4200"]'
    result = subprocess.run(
        [sys.executable, "-m", "app.db.check"],
        cwd=Path(__file__).resolve().parents[1],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )

    assert result.returncode == 1
    assert "DATABASE_URL" in result.stderr
    assert "Traceback" not in result.stderr
