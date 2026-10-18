import hashlib
import hmac
from datetime import timedelta
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import delete, select, case
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.core.security import PASSWORDS, DUMMY_HASH, now, secret, issue_token, SESSION_SECONDS
from app.models import Administrador
from app.models.auth import LimiteRequisicao, SessaoAdministrativa


def limit_requests(engine, settings, scope, identity, maximum, seconds):
    """Contador atômico no PostgreSQL, independente de worker e do resultado HTTP."""
    key = hmac.new(secret(settings).encode(), f'{scope}:{identity}'.encode(), hashlib.sha256).hexdigest()
    current = now()
    cutoff = current - timedelta(seconds=seconds)
    table = LimiteRequisicao
    statement = insert(table).values(chave=key, janela=current, tentativas=1)
    statement = statement.on_conflict_do_update(index_elements=[table.chave], set_={
        'janela': case((table.janela <= cutoff, current), else_=table.janela),
        'tentativas': case((table.janela <= cutoff, 1), else_=table.tentativas + 1),
    }).returning(table.tentativas)
    with Session(engine) as session, session.begin():
        session.execute(delete(table).where(table.janela < current - timedelta(days=1)))
        count = session.scalar(statement)
    if count > maximum:
        raise HTTPException(429, 'Limite de tentativas atingido. Tente novamente mais tarde.',
            headers={'Retry-After': str(seconds)})


def login(session, settings, email, password):
    secret(settings)
    admin = session.scalar(select(Administrador).where(Administrador.email == email))
    valid = PASSWORDS.verify(password, admin.senha_hash if admin else DUMMY_HASH)
    if not valid or admin is None:
        raise HTTPException(401, 'E-mail ou senha inválidos.')
    expires = now() + timedelta(seconds=SESSION_SECONDS)
    session.execute(delete(SessaoAdministrativa).where(SessaoAdministrativa.expira_em <= now()))
    record = SessaoAdministrativa(id=uuid4(), administrador_id=admin.id, expira_em=expires)
    session.add(record)
    session.flush()
    return admin, record, issue_token(settings, admin.id, record.id, expires)


def create_first_admin(session, nome, email, password):
    from sqlalchemy import text
    # Serializa dois processos de bootstrap concorrentes sem criar novos papéis.
    session.execute(text('SELECT pg_advisory_xact_lock(84723019)'))
    if session.scalar(select(Administrador.id).limit(1)) is not None:
        raise ValueError('A administradora já existe; o bootstrap não altera credenciais.')
    if len(password) < 12 or len(password) > 128:
        raise ValueError('A senha deve conter entre 12 e 128 caracteres.')
    admin = Administrador(nome=nome, email=email, senha_hash=PASSWORDS.hash(password))
    session.add(admin)
    session.flush()
    return admin
