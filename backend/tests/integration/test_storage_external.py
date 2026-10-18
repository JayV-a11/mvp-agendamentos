"""Teste opt-in: banco local isolado e objetos UUID exclusivos no Storage real.

Não é simulação de Storage. Não cria serviços ou agendamentos no banco Supabase.
"""
from io import BytesIO

import httpx2
from PIL import Image
import pytest

from app.core.config import Settings
from app.services.photos import Storage, photo_version
from tests.integration.test_api import api, password_hash, authenticate, service

pytestmark = pytest.mark.integration


def test_fotos_reais_upload_substituicao_privacidade_e_remocao(api, request):
    if not request.config.getoption('--storage-external'):
        pytest.skip('Storage externo requer --storage-external e configuração local explícita.')
    actual = Settings()
    if not actual.supabase_url or not actual.supabase_service_key:
        pytest.fail('Preencha SUPABASE_URL e SUPABASE_SERVICE_KEY somente no .env local.')
    for key in ['supabase_url','supabase_service_key','storage_bucket']:
        setattr(api.settings, key, getattr(actual, key))
    authenticate(api)
    s = service(api)
    owner, sid = api.admin_id, s['id']
    storage = Storage(actual)
    versions = []
    try:
        for color in ['white','black']:
            source = BytesIO()
            Image.new('RGB',(32,32),color).save(source,format='PNG')
            response = api.put(f'/admin/servicos/{sid}/foto', content=source.getvalue(),
                headers={'Content-Type':'image/png'})
            assert response.status_code == 200, response.text
            url = response.json()['imagem_url']
            versions.append(photo_version(url))
            photo = api.get(url)
            assert photo.status_code == 200 and photo.headers['content-type'] == 'image/webp'
            with Image.open(BytesIO(photo.content)) as image:
                assert image.format == 'WEBP'
            objects = storage.call('POST', f'/object/list/{storage.bucket}',
                json={'prefix':f'{owner}/{sid}', 'limit':100}).json()
            assert len(objects) == 1
        assert versions[0] != versions[1]
        with httpx2.Client(timeout=20) as client:
            public = client.get(storage.url + storage.path(owner,sid,versions[-1]).replace(
                '/object/', '/object/public/', 1))
            assert not public.is_success
        response = api.put(f'/admin/servicos/{sid}', json={'nome':s['nome'], 'preco':s['preco'],
            'duracao_minutos':s['duracao_minutos'], 'ativo':False})
        assert response.status_code == 200
        assert api.get(f'/publico/servicos/{sid}/foto').status_code == 409
        assert api.get(f'/admin/servicos/{sid}/foto').status_code == 200
        assert api.delete(f'/admin/servicos/{sid}/foto').status_code == 200
        assert api.get(f'/admin/servicos/{sid}/foto').status_code == 404
        assert storage.call('POST', f'/object/list/{storage.bucket}',
            json={'prefix':f'{owner}/{sid}', 'limit':100}).json() == []
    finally:
        # Remove somente os nomes aleatórios conhecidos deste teste, sem listar bucket.
        for version in versions:
            storage.delete(owner,sid,version)
