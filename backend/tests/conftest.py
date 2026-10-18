import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def pytest_addoption(parser):
    parser.addoption(
        "--postgres-bin", default=None,
        help="Diretório com initdb e pg_ctl para um cluster de testes local temporário.",
    )
    parser.addoption('--storage-external', action='store_true', default=False,
        help='Autoriza verificar fotos no Storage real usando somente objetos UUID dos testes isolados.')


@pytest.fixture
def client():
    settings = Settings(_env_file=None, cors_origins=["http://localhost:4200"])
    with TestClient(create_app(settings)) as test_client:
        yield test_client
