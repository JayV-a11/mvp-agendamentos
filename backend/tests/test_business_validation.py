from io import BytesIO

from fastapi import HTTPException
from PIL import Image
from pydantic import ValidationError
import pytest

from app.core.config import Settings
from app.services.photos import normalize_photo


@pytest.mark.parametrize('format,mime', [('JPEG','image/jpeg'), ('PNG','image/png'), ('WEBP','image/webp')])
def test_foto_real_decodificada_regravada_sem_metadados(format, mime):
    source = BytesIO()
    Image.new('RGB', (1800, 100), 'white').save(source, format=format)
    data = normalize_photo(source.getvalue() + b'conteudo-anexado-nao-confiavel', mime)
    with Image.open(BytesIO(data)) as image:
        assert image.format == 'WEBP' and image.width == 1600
        assert not image.getexif()
    assert b'conteudo-anexado-nao-confiavel' not in data


@pytest.mark.parametrize('data,mime,status', [(b'MZexecutavel', 'image/png', 422),
    (b'<svg/>','image/svg+xml',415), (b'x'*(5*1024*1024+1),'image/jpeg',413)],
    ids=['executavel-disfarcado', 'tipo-nao-permitido', 'acima-de-5mb'])
def test_foto_invalida_rejeitada(data,mime,status):
    with pytest.raises(HTTPException) as error:
        normalize_photo(data,mime)
    assert error.value.status_code == status


def test_mime_diferente_do_conteudo_rejeitado():
    source = BytesIO()
    Image.new('RGB',(8,8)).save(source,format='PNG')
    with pytest.raises(HTTPException):
        normalize_photo(source.getvalue(),'image/jpeg')


@pytest.mark.parametrize('overrides', [{'jwt_secret':'curto'},
    {'environment':'production'}, {'cookie_samesite':'none'},
    {'supabase_url':'http://storage.test'}, {'supabase_url':'https://user:pass@storage.test'},
    {'business_timezone':'fuso-inexistente'}, {'storage_bucket':'../outro'}])
def test_configuracoes_inseguras_rejeitadas(overrides):
    with pytest.raises(ValidationError):
        Settings(_env_file=None, **overrides)


def test_producao_exige_https_e_secure():
    settings = Settings(_env_file=None, environment='production', cookie_secure=True,
        cookie_samesite='none', jwt_secret='s'*64, cors_origins=['https://app.example.test'],
        database_url='postgresql+psycopg://user:pass@host/db')
    assert settings.cookie_secure and settings.cookie_samesite == 'none'
