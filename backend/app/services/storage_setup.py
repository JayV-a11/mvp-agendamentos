"""Configura somente o bucket privado do MVP, preservando arquivos existentes."""
import argparse
from fastapi import HTTPException
import httpx2

from app.core.config import Settings
from app.services.photos import Storage


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--configure-existing', action='store_true',
        help='Aplica limites de 5 MB/WebP somente ao bucket já privado configurado.')
    configure = parser.parse_args().configure_existing
    try:
        settings = Settings()
        storage = Storage(settings)
        with httpx2.Client(timeout=20, follow_redirects=False) as client:
            response = client.get(storage.url + '/bucket/' + storage.bucket, headers=storage.headers)
            if response.status_code == 404 or (response.status_code == 400 and
                    response.json().get('message') == 'Bucket not found'):
                response = client.post(storage.url + '/bucket', headers=storage.headers,
                    json={'id': storage.bucket, 'name': storage.bucket, 'public': False,
                        'file_size_limit': 5 * 1024 * 1024, 'allowed_mime_types': ['image/webp']})
                if not response.is_success:
                    raise HTTPException(503, 'Não foi possível criar o bucket.')
                response = client.get(storage.url + '/bucket/' + storage.bucket, headers=storage.headers)
            if not response.is_success:
                raise HTTPException(503, 'Não foi possível verificar o bucket.')
            data = response.json()
            if configure and data.get('public') is False:
                response = client.put(storage.url + '/bucket/' + storage.bucket, headers=storage.headers,
                    json={'file_size_limit': 5 * 1024 * 1024, 'allowed_mime_types': ['image/webp']})
                if not response.is_success:
                    raise HTTPException(503, 'Não foi possível configurar os limites.')
                response = client.get(storage.url + '/bucket/' + storage.bucket, headers=storage.headers)
                if not response.is_success:
                    raise HTTPException(503, 'Não foi possível verificar os limites.')
                data = response.json()
            if data.get('public') is not False or data.get('allowed_mime_types') != ['image/webp'] or data.get('file_size_limit') != 5 * 1024 * 1024:
                print('Bucket existente com configuração diferente. Nenhuma alteração realizada.')
                print('Exija bucket privado, limite 5242880 bytes e somente image/webp.')
                return 1
        print('Bucket privado verificado: 5 MB, somente WebP otimizado pelo backend.')
        print('Não crie políticas para anon/authenticated em storage.objects para este bucket.')
        return 0
    except (HTTPException, httpx2.HTTPError, ValueError):
        print('Storage não configurado ou inacessível. Confira as variáveis locais e a chave service_role.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
