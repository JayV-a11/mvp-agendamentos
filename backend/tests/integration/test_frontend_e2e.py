"""Integração Angular + FastAPI + PostgreSQL locais, sem mocks de endpoints."""
import os
import base64
from io import BytesIO
from pathlib import Path
import secrets
import socket
import subprocess
import sys
from threading import Thread
import time

from fastapi import FastAPI
from starlette.exceptions import HTTPException
from starlette.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import pytest
import uvicorn
from PIL import Image
from sqlalchemy import select

from app.core.config import Settings
from app.main import create_app
from app.services.auth import create_first_admin
from app.models import Servico
from app.services.photos import Storage, photo_version

pytestmark = pytest.mark.integration


def test_fluxo_completo_angular_com_api_e_postgresql(db, request):
    if not request.config.getoption('--frontend-e2e'):
        pytest.skip('Navegador exige --frontend-e2e e build Angular.')
    root = Path(__file__).resolve().parents[3]
    frontend = root / 'frontend'
    dist = frontend / 'dist/frontend/browser'
    if not (dist / 'index.html').exists():
        pytest.fail('Execute npm run build em frontend/ antes do teste de navegador.')
    password = secrets.token_urlsafe(24)
    email = 'administradora-e2e@example.test'
    with Session(db) as session, session.begin():
        admin = create_first_admin(session, 'Administradora de teste E2E', email, password)
        admin_id = admin.id
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    origin = f'http://127.0.0.1:{port}'
    settings = Settings(_env_file=None, jwt_secret=secrets.token_urlsafe(48),cors_origins=[origin])
    external_storage = request.config.getoption('--storage-external')
    if external_storage:
        actual = Settings()
        for field in ('supabase_url','supabase_service_key','storage_bucket'):
            setattr(settings, field, getattr(actual, field))

    class SPA(StaticFiles):
        async def get_response(self, path, scope):
            try:
                return await super().get_response(path, scope)
            except HTTPException as error:
                if error.status_code != 404:
                    raise
                return await super().get_response('index.html', scope)

    app = FastAPI()
    app.mount('/api', create_app(settings, engine=db))
    app.mount('/', SPA(directory=dist, html=True))
    server = uvicorn.Server(uvicorn.Config(app,host='127.0.0.1',port=port,log_level='critical',access_log=False))
    thread = Thread(target=server.run,kwargs={'sockets':[sock]},daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while not server.started:
            if time.monotonic() > deadline or not thread.is_alive():
                pytest.fail('Servidor local de integração não iniciou.')
            time.sleep(0.01)
        env = {**os.environ,'E2E_ISOLATED':'1','E2E_BASE_URL':origin,
               'E2E_EMAIL':email,'E2E_PASSWORD':password,'E2E_STORAGE':'1' if external_storage else '0'}
        photo = BytesIO()
        Image.new('RGB', (32,32), '#eac5d2').save(photo,format='PNG')
        env['E2E_PHOTO_BASE64'] = base64.b64encode(photo.getvalue()).decode('ascii')
        env.pop('NO_COLOR', None)
        env.pop('FORCE_COLOR', None)
        node = os.environ.get('NODE_BINARY') or 'node'
        cli = frontend/'node_modules/@playwright/test/cli.js'
        result = subprocess.run([node,str(cli),'test'],cwd=frontend,env=env,timeout=180,
            capture_output=True,text=True,encoding='utf-8',errors='replace')
        # Nunca exibir a senha aleatória mesmo em falha inesperada do runner.
        output = (result.stdout + result.stderr).replace(password,'[senha de teste omitida]')
        print(output.encode(sys.stdout.encoding or 'utf-8',errors='replace').decode(sys.stdout.encoding or 'utf-8'))
        assert result.returncode == 0, 'Teste de navegador falhou; consulte a saída e o relatório Playwright.'
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        sock.close()
        if external_storage:
            with Session(db) as session:
                for record in session.scalars(select(Servico).where(Servico.administrador_id == admin_id)):
                    if record.imagem_url:
                        Storage(settings).delete(admin_id,record.id,photo_version(record.imagem_url))
        assert not thread.is_alive()
