import warnings
import logging
from io import BytesIO
from urllib.parse import urlsplit, parse_qs
from uuid import UUID, uuid4

import httpx2
from fastapi import HTTPException
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy import event

from app.core.http import MAX_PHOTO
from app.repositories import catalogo
from app.services.agenda import require

TYPES = {'image/jpeg': 'JPEG', 'image/png': 'PNG', 'image/webp': 'WEBP'}
MAX_PIXELS = 20_000_000


def normalize_photo(data: bytes, content_type: str):
    if len(data) > MAX_PHOTO:
        raise HTTPException(413, 'A foto deve ter no máximo 5 MB.')
    if content_type not in TYPES:
        raise HTTPException(415, 'Envie uma foto JPEG, PNG ou WebP.')
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as image:
                if image.format != TYPES[content_type] or image.width * image.height > MAX_PIXELS:
                    raise ValueError()
                image.verify()
            with Image.open(BytesIO(data)) as image:
                normalized = ImageOps.exif_transpose(image).convert('RGB')
                normalized.thumbnail((1600, 1600))
                output = BytesIO()
                normalized.save(output, 'WEBP', quality=82, method=4)
                return output.getvalue()
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError,
            Image.DecompressionBombWarning, Image.DecompressionBombError):
        raise HTTPException(422, 'Foto inválida, corrompida ou com dimensões excessivas.') from None


class Storage:
    def __init__(self, settings):
        if settings.supabase_url is None or settings.supabase_service_key is None:
            raise HTTPException(503, 'Armazenamento de fotos ainda não configurado.')
        self.url = f'{settings.supabase_url}/storage/v1'
        self.bucket = settings.storage_bucket
        key = settings.supabase_service_key.get_secret_value()
        self.headers = {'apikey': key, 'Authorization': f'Bearer {key}'}

    def call(self, method, path, **kwargs):
        try:
            with httpx2.Client(timeout=20, follow_redirects=False) as client:
                response = client.request(method, self.url + path, headers=self.headers, **kwargs)
            if not response.is_success:
                raise HTTPException(503, 'Falha no armazenamento de fotos. Tente novamente.')
            return response
        except httpx2.HTTPError:
            raise HTTPException(503, 'Não foi possível acessar o armazenamento de fotos.') from None

    def path(self, owner, service_id, version):
        # Somente UUIDs validados, nunca nome de arquivo ou caminho fornecido no upload.
        return f'/object/{self.bucket}/{owner}/{service_id}/{version}.webp'

    def upload(self, owner, service_id, version, data):
        headers = self.headers.copy()
        headers.update({'Content-Type': 'image/webp', 'x-upsert': 'false', 'cache-control': '60'})
        try:
            with httpx2.Client(timeout=20, follow_redirects=False) as client:
                response = client.post(self.url + self.path(owner, service_id, version), headers=headers, content=data)
            if not response.is_success:
                raise HTTPException(503, 'Falha ao armazenar a foto. Tente novamente.')
        except httpx2.HTTPError:
            raise HTTPException(503, 'Não foi possível acessar o armazenamento de fotos.') from None

    def download(self, owner, service_id, version):
        # A API permite obter objetos privados com o token do backend.
        path = self.path(owner, service_id, version).replace('/object/', '/object/authenticated/', 1)
        return self.call('GET', path).content

    def delete(self, owner, service_id, version):
        self.call('DELETE', f'/object/{self.bucket}', json={'prefixes': [f'{owner}/{service_id}/{version}.webp']})


def photo_version(url):
    try:
        return UUID(parse_qs(urlsplit(url).query)['versao'][0])
    except (KeyError, ValueError, TypeError):
        raise HTTPException(503, 'Referência de foto inválida.') from None


def cleanup_after(db, event_name, storage, owner, service_id, version):
    def cleanup(session):
        try:
            storage.delete(owner, service_id, version)
        except HTTPException:
            # A referência transacional permanece correta; arquivo privado pode
            # exigir remoção operacional se o Storage estiver indisponível.
            logging.getLogger(__name__).warning('Limpeza de foto privada pendente no Storage.')
    event.listen(db, event_name, cleanup, once=True)


def upload_photo(db, settings, owner, service_id, data, content_type):
    record = require(catalogo.service(db, service_id, owner, lock=True))
    normalized = normalize_photo(data, content_type)
    storage = Storage(settings)
    version = uuid4()
    storage.upload(owner, service_id, version, normalized)
    cleanup_after(db, 'after_rollback', storage, owner, service_id, version)
    if record.imagem_url is not None:
        cleanup_after(db, 'after_commit', storage, owner, service_id, photo_version(record.imagem_url))
    # A referência é sempre relativa à API; não aceita URLs arbitrárias ou SSRF.
    record.imagem_url = f'/publico/servicos/{service_id}/foto?versao={version}'
    db.flush()
    return record


def delete_photo(db, settings, owner, service_id):
    record = require(catalogo.service(db, service_id, owner, lock=True))
    storage = Storage(settings)
    if record.imagem_url is not None:
        cleanup_after(db, 'after_commit', storage, owner, service_id, photo_version(record.imagem_url))
    record.imagem_url = None
    db.flush()
    return record
