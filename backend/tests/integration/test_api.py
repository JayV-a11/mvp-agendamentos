from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from io import BytesIO
import socket
from threading import Barrier, Thread
import time
from uuid import uuid4

import httpx2
import jwt
import pytest
from PIL import Image
from sqlalchemy import select, insert, text, update
from sqlalchemy.orm import Session
import uvicorn

from app.core.config import Settings
from app.core.security import COOKIE, PASSWORDS, now, issue_token
from app.main import create_app
from app.models import Administrador, Agendamento, Servico, HorarioDisponivel
from app.models.auth import SessaoAdministrativa
from app.services.auth import create_first_admin

pytestmark = pytest.mark.integration
PASSWORD = 'Senha-sintetica-exclusiva-123'
EMAIL = 'admin@example.test'


@pytest.fixture(scope='session')
def password_hash():
    return PASSWORDS.hash(PASSWORD)


@pytest.fixture
def api(db, password_hash):
    settings = Settings(_env_file=None, jwt_secret='s' * 64)
    with Session(db) as session, session.begin():
        admin = Administrador(nome='Administradora de teste', email=EMAIL, senha_hash=password_hash)
        session.add(admin)
        session.flush()
        admin_id = admin.id
    app = create_app(settings, engine=db)
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    server = uvicorn.Server(uvicorn.Config(app, host='127.0.0.1', port=port,
        log_level='critical', access_log=False))
    thread = Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
    thread.start()
    try:
        deadline = time.monotonic() + 10
        while not server.started:
            if time.monotonic() > deadline or not thread.is_alive():
                pytest.fail('Servidor HTTP local de teste não iniciou.')
            time.sleep(0.01)
        with httpx2.Client(base_url=f'http://127.0.0.1:{port}', timeout=20) as client:
            client.admin_id = admin_id
            client.settings = settings
            yield client
    finally:
        server.should_exit = True
        thread.join(timeout=15)
        sock.close()
        assert not thread.is_alive()


def authenticate(api):
    response = api.post('/auth/login', json={'email': EMAIL, 'senha': PASSWORD})
    assert response.status_code == 200, response.text
    api.headers['X-CSRF-Token'] = response.json()['csrf_token']
    return response


def service(api, **overrides):
    data = {'nome': 'Trança sintética', 'preco': '125.50', 'duracao_minutos': 60,
        'descricao': None, 'ativo': True, **overrides}
    response = api.post('/admin/servicos', json=data)
    assert response.status_code == 201, response.text
    return response.json()


def slot(api, offset=0, minutes=120):
    start = now() + timedelta(days=7, hours=offset)
    response = api.post('/admin/horarios', json={'inicio': start.isoformat(),
        'fim': (start + timedelta(minutes=minutes)).isoformat()})
    assert response.status_code == 201, response.text
    return response.json()


def booking(api, service, slot, **overrides):
    return api.post('/publico/agendamentos', json={'servico_id': service['id'],
        'horario_id': slot['id'], 'cliente_nome': 'Cliente sintética',
        'cliente_telefone': '(11) 99999-0000', **overrides})


def transition(api, booking_id, target):
    return api.patch(f'/admin/agendamentos/{booking_id}/status', json={'status': target})


def test_fluxo_http_completo_catalogo_reserva_aprovacao_recusa_cancelamento(api, db):
    response = authenticate(api)
    assert 'httponly' in response.headers['set-cookie'].lower()
    assert 'samesite=lax' in response.headers['set-cookie'].lower()
    assert 'senha' not in response.text and 'eyJ' not in response.text
    assert api.get('/auth/sessao').json()['csrf_token'] == api.headers['X-CSRF-Token']
    s, h = service(api), slot(api)
    assert [r['id'] for r in api.get('/publico/servicos').json()] == [s['id']]
    assert len(api.get(f"/publico/servicos/{s['id']}/horarios").json()) == 1
    result = booking(api, s, h)
    assert result.status_code == 201
    bid = result.json()['id']
    assert result.json()['status'] == 'pendente'
    assert 'pendente' in result.json()['mensagem']
    assert 'cliente_telefone' not in result.json()
    assert api.get(f"/publico/servicos/{s['id']}/horarios").json() == []
    assert booking(api, s, h).status_code == 409
    items = api.get('/admin/agendamentos', params={'status': 'pendente'}).json()
    assert items[0]['cliente_telefone'] == '11999990000'
    assert items[0]['preco_solicitado'] == '125.50'
    edited = api.put(f"/admin/servicos/{s['id']}", json={
        'nome': s['nome'], 'preco': '200.00', 'duracao_minutos': 90, 'ativo': False})
    assert edited.status_code == 200
    assert api.get('/publico/servicos').json() == []
    assert booking(api, s, h).status_code == 409
    assert transition(api, bid, 'aprovado').status_code == 200
    assert transition(api, bid, 'aprovado').status_code == 409
    assert transition(api, bid, 'recusado').status_code == 409
    assert transition(api, bid, 'cancelado').status_code == 200
    assert transition(api, bid, 'aprovado').status_code == 409
    api.put(f"/admin/servicos/{s['id']}", json={
        'nome': s['nome'], 'preco': '200', 'duracao_minutos': 90, 'ativo': True})
    assert len(api.get(f"/publico/servicos/{s['id']}/horarios").json()) == 1
    bid2 = booking(api, s, h).json()['id']
    assert transition(api, bid2, 'recusado').status_code == 200
    assert len(api.get(f"/publico/servicos/{s['id']}/horarios").json()) == 1
    with Session(db) as session:
        record = session.get(Agendamento, bid)
        assert str(record.preco_solicitado) == '125.50'
        assert record.duracao_minutos_solicitada == 60


@pytest.mark.parametrize('method,path,payload', [
    ('GET', '/admin/servicos', None), ('POST', '/admin/servicos', {}),
    ('PUT', f'/admin/servicos/{uuid4()}', {}), ('GET', '/admin/horarios', None),
    ('POST', '/admin/horarios', {}), ('PATCH', f'/admin/horarios/{uuid4()}/bloqueio', {}),
    ('GET', '/admin/agendamentos', None), ('PATCH', f'/admin/agendamentos/{uuid4()}/status', {}),
    ('PUT', f'/admin/servicos/{uuid4()}/foto', None),
    ('DELETE', f'/admin/servicos/{uuid4()}/foto', None),
    ('GET', f'/admin/servicos/{uuid4()}/foto', None),
])
def test_endpoints_administrativos_exigem_autenticacao(api, method, path, payload):
    response = api.request(method, path, json=payload)
    assert response.status_code == 401, response.text


def test_csrf_origem_logout_e_reutilizacao(api):
    authenticate(api)
    old_cookie = api.cookies.get(COOKIE)
    csrf = api.headers.pop('X-CSRF-Token')
    assert api.post('/admin/servicos', json={}).status_code == 403
    api.headers['X-CSRF-Token'] = csrf
    assert api.post('/admin/servicos', json={}, headers={'Origin': 'https://evil.test'}).status_code == 403
    assert api.post('/auth/logout').status_code == 204
    assert api.get('/auth/sessao').status_code == 401
    api.cookies.set(COOKIE, old_cookie)
    assert api.get('/auth/sessao').status_code == 401


@pytest.mark.parametrize('kind', ['invalid', 'expired', 'signature', 'algorithm', 'no-session'])
def test_jwt_invalido_nao_autoriza(api, kind):
    authenticate(api)
    token = api.cookies.get(COOKIE)
    claims = jwt.decode(token, api.settings.jwt_secret.get_secret_value(), algorithms=['HS256'],
        audience='administracao', issuer='agendamentos')
    if kind == 'invalid':
        token = 'token-invalido'
    else:
        if kind == 'expired':
            claims['exp'] = now() - timedelta(seconds=1)
        if kind == 'no-session':
            claims['jti'] = str(uuid4())
        token = jwt.encode(claims, 'x' * 64 if kind == 'signature' else 's' * 64,
            algorithm='HS384' if kind == 'algorithm' else 'HS256')
    api.cookies.clear()
    api.cookies.set(COOKIE, token)
    assert api.get('/admin/agendamentos').status_code == 401


def test_login_generico_limite_persistente_e_origem(api, db):
    assert api.post('/auth/login', json={'email': EMAIL, 'senha': PASSWORD},
        headers={'Origin': 'https://evil.test'}).status_code == 403
    errors = []
    for email in [EMAIL, 'ausente@example.test']:
        errors.append(api.post('/auth/login', json={'email': email, 'senha': 'errada'}).json())
    assert errors[0] == errors[1] == {'detail': 'E-mail ou senha inválidos.'}
    for _ in range(4):
        assert api.post('/auth/login', json={'email': EMAIL, 'senha': 'errada'}).status_code == 401
    response = api.post('/auth/login', json={'email': EMAIL, 'senha': PASSWORD})
    assert response.status_code == 429 and response.headers['retry-after'] == '900'
    with db.connect() as connection:
        assert connection.execute(text('SELECT count(*) FROM limites_requisicoes')).scalar_one() > 0


def test_bloqueio_duracao_passado_sobreposicao_timezone(api, db):
    authenticate(api)
    s, h = service(api), slot(api)
    assert api.post('/admin/horarios', json={'inicio': h['inicio'], 'fim': h['fim']}).status_code == 409
    assert api.post('/admin/horarios', json={'inicio': '2030-01-01T10:00:00', 'fim': '2030-01-01T11:00:00'}).status_code == 422
    assert api.post('/admin/horarios', json={'inicio': h['fim'], 'fim': h['inicio']}).status_code == 422
    assert api.patch(f"/admin/horarios/{h['id']}/bloqueio", json={'bloqueado': True}).status_code == 200
    assert booking(api, s, h).status_code == 409
    assert api.get(f"/publico/servicos/{s['id']}/horarios").json() == []
    api.patch(f"/admin/horarios/{h['id']}/bloqueio", json={'bloqueado': False})
    short = slot(api, offset=3, minutes=30)
    assert booking(api, s, short).status_code == 409
    assert len(api.get(f"/publico/servicos/{s['id']}/horarios").json()) == 1
    with db.begin() as connection:
        connection.execute(update(HorarioDisponivel).where(HorarioDisponivel.id == h['id']).values(
            inicio=now() - timedelta(hours=3), fim=now() - timedelta(hours=1)))
    assert booking(api, s, h).status_code == 409
    assert api.get(f"/publico/servicos/{s['id']}/horarios").json() == []


@pytest.mark.parametrize('release', ['recusado', 'cancelado'])
def test_liberacao_nao_remove_bloqueio_explicito(api, release):
    authenticate(api)
    s, h = service(api), slot(api)
    bid = booking(api, s, h).json()['id']
    api.patch(f"/admin/horarios/{h['id']}/bloqueio", json={'bloqueado': True})
    assert transition(api, bid, release).status_code == 200
    assert booking(api, s, h).status_code == 409
    assert api.get(f"/publico/servicos/{s['id']}/horarios").json() == []


def test_reservas_http_simultaneas_uma_criada_outra_conflito(api, db):
    authenticate(api)
    s, h = service(api), slot(api)
    barrier = Barrier(2)
    def attempt():
        with httpx2.Client(base_url=str(api.base_url), timeout=20) as other:
            barrier.wait(timeout=10)
            return booking(other, s, h).status_code
    with ThreadPoolExecutor(max_workers=2) as executor:
        result = list(executor.map(lambda _: attempt(), range(2)))
    assert sorted(result) == [201, 409]
    with db.connect() as connection:
        assert connection.execute(text('SELECT count(*) FROM agendamentos')).scalar_one() == 1


def test_decisoes_http_simultaneas_preservam_transicao(api):
    authenticate(api)
    s, h = service(api), slot(api)
    bid = booking(api, s, h).json()['id']
    barrier = Barrier(2)
    cookie_value = api.cookies.get(COOKIE)
    csrf = api.headers['X-CSRF-Token']
    def attempt(target):
        with httpx2.Client(base_url=str(api.base_url), timeout=20,
                headers={'X-CSRF-Token': csrf, 'Cookie': f'{COOKIE}={cookie_value}'}) as other:
            barrier.wait(timeout=10)
            return transition(other, bid, target).status_code
    with ThreadPoolExecutor(max_workers=2) as executor:
        result = list(executor.map(attempt, ['aprovado', 'recusado']))
    assert sorted(result) == [200, 409]


def test_troca_de_ids_e_privacidade(api, db, password_hash):
    authenticate(api)
    with db.begin() as connection:
        owner = connection.execute(insert(Administrador).values(nome='Outro registro de teste',
            email='outro@example.test', senha_hash=password_hash).returning(Administrador.id)).scalar_one()
        sid = connection.execute(insert(Servico).values(administrador_id=owner, nome='Outro serviço',
            preco=100, duracao_minutos=30).returning(Servico.id)).scalar_one()
        hid = connection.execute(insert(HorarioDisponivel).values(administrador_id=owner,
            inicio=now()+timedelta(days=7), fim=now()+timedelta(days=7, hours=2)).returning(HorarioDisponivel.id)).scalar_one()
    assert api.put(f'/admin/servicos/{sid}', json={'nome':'Ataque', 'preco':1, 'duracao_minutos':1}).status_code == 404
    assert api.patch(f'/admin/horarios/{hid}/bloqueio', json={'bloqueado':True}).status_code == 404
    s = service(api)
    assert booking(api, s, {'id':str(hid)}).status_code == 404
    api.cookies.clear()
    assert api.get('/admin/agendamentos').status_code == 401
    assert api.get('/publico/agendamentos').status_code == 405
    assert 'cliente_telefone' not in api.get('/publico/servicos').text


@pytest.mark.parametrize('field,value', [('preco', 'NaN'), ('preco', '-1'), ('preco', '1.001'),
    ('duracao_minutos', 0), ('duracao_minutos', True), ('nome', '  '), ('imagem_url', 'https://evil.test')])
def test_validacao_servicos(api, field, value):
    authenticate(api)
    response = api.post('/admin/servicos', json={'nome':'Teste', 'preco':'50', 'duracao_minutos':30, field:value})
    assert response.status_code == 422
    assert value is True or str(value) not in response.text or field == 'duracao_minutos'


def test_injecao_tratada_como_texto_e_sem_reflexao_de_senha(api, db):
    authenticate(api)
    name = "<script>alert(1)</script>'; DROP TABLE servicos; --"
    s = service(api, nome=name)
    assert api.get('/publico/servicos').json()[0]['nome'] == name
    with db.connect() as connection:
        assert connection.execute(text('SELECT count(*) FROM servicos')).scalar_one() == 1
    response = api.post('/auth/login', json={'email': EMAIL, 'senha': 'SEGREDO' * 100})
    assert response.status_code == 422 and 'SEGREDO' not in response.text
    assert api.post('/publico/agendamentos', content=b'x'*65537,
        headers={'Content-Type': 'application/json'}).status_code == 413


def test_foto_sem_configuracao_nao_finge_upload(api):
    authenticate(api)
    s = service(api)
    output = BytesIO()
    Image.new('RGB', (8, 8), 'white').save(output, format='PNG')
    response = api.put(f"/admin/servicos/{s['id']}/foto", content=output.getvalue(), headers={'Content-Type':'image/png'})
    assert response.status_code == 503
    assert api.get('/publico/servicos').json()[0]['imagem_url'] is None
    assert api.get(f"/publico/servicos/{s['id']}/foto").status_code == 404


def test_bootstrap_recusa_segunda_administradora(api, db):
    with Session(db) as session, session.begin(), pytest.raises(ValueError):
        create_first_admin(session, 'Segunda', 'segunda@example.test', PASSWORD)


def test_bootstrap_concorrente_cria_uma_administradora_com_hash_argon2(db):
    barrier = Barrier(2)
    def attempt():
        barrier.wait(timeout=10)
        try:
            with Session(db) as session, session.begin():
                create_first_admin(session, 'Administradora sintética', EMAIL, PASSWORD)
            return 'criada'
        except ValueError:
            return 'recusada'
    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(lambda _: attempt(), range(2))) == ['criada','recusada']
    with Session(db) as session:
        records = list(session.scalars(select(Administrador)))
        assert len(records) == 1
        assert records[0].senha_hash.startswith('$argon2id$')
        assert PASSWORD not in records[0].senha_hash
        assert PASSWORDS.verify(PASSWORD, records[0].senha_hash)


def test_tabelas_tecnicas_sem_acesso_direto(api, db):
    with db.connect() as connection:
        for table in ['sessoes_administrativas', 'limites_requisicoes']:
            assert connection.execute(text('SELECT relrowsecurity FROM pg_class WHERE oid=CAST(:t AS regclass)'),
                {'t':f'public.{table}'}).scalar_one()
            for role in ['anon', 'authenticated', 'service_role']:
                assert not connection.execute(text("SELECT has_table_privilege(:r,:t,'SELECT,INSERT,UPDATE,DELETE')"),
                    {'r':role,'t':f'public.{table}'}).scalar_one()


def test_falha_no_commit_nao_retorna_sucesso_http(api, db):
    authenticate(api)
    with db.begin() as connection:
        connection.execute(text("""CREATE FUNCTION public.falhar_commit_teste() RETURNS trigger
            LANGUAGE plpgsql AS $$ BEGIN RAISE EXCEPTION 'falha sintética' USING ERRCODE='23514'; END $$"""))
        connection.execute(text('CREATE CONSTRAINT TRIGGER falhar_commit_teste AFTER INSERT ON servicos '
            'DEFERRABLE INITIALLY DEFERRED FOR EACH ROW EXECUTE FUNCTION public.falhar_commit_teste()'))
    try:
        response = api.post('/admin/servicos', json={'nome':'Teste', 'preco':'50','duracao_minutos':30})
        assert response.status_code == 409
        assert 'falha sintética' not in response.text
        with db.connect() as connection:
            assert connection.execute(text('SELECT count(*) FROM servicos')).scalar_one() == 0
    finally:
        with db.begin() as connection:
            connection.execute(text('DROP TRIGGER falhar_commit_teste ON servicos'))
            connection.execute(text('DROP FUNCTION public.falhar_commit_teste()'))
