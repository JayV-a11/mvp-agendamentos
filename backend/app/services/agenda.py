from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import select

from app.core.security import now
from app.models import Agendamento, HorarioDisponivel, Servico
from app.repositories import catalogo


def require(record, message='Registro não encontrado.'):
    if record is None:
        raise HTTPException(404, message)
    return record


def active_service(db, service_id, lock=False):
    record = require(catalogo.service(db, service_id, lock=lock), 'Serviço não encontrado.')
    if not record.ativo:
        raise HTTPException(409, 'Este serviço não está disponível para novas solicitações.')
    return record


def create_service(db, owner, data):
    record = Servico(administrador_id=owner, **data.model_dump())
    db.add(record)
    db.flush()
    return record


def update_service(db, owner, service_id, data):
    record = require(catalogo.service(db, service_id, owner, lock=True))
    for key, value in data.model_dump().items():
        setattr(record, key, value)
    db.flush()
    return record


def create_slot(db, owner, data):
    if data.inicio <= now():
        raise HTTPException(422, 'O horário deve começar no futuro.')
    record = HorarioDisponivel(administrador_id=owner, **data.model_dump())
    db.add(record)
    db.flush()
    return record


def block_slot(db, owner, slot_id, blocked):
    record = require(catalogo.slot(db, slot_id, owner, lock=True))
    record.bloqueado = blocked
    db.flush()
    return record


def assert_available(db, record, duration):
    if (record.bloqueado or record.inicio <= now()
            or timedelta(minutes=duration) > record.fim - record.inicio
            or catalogo.occupied(db, record.id)):
        raise HTTPException(409, 'Horário indisponível. Escolha outro horário.')


def request_booking(db, data):
    # Bloqueios no serviço e no bloco serializam desativação, bloqueio e reserva.
    service = active_service(db, data.servico_id, lock=True)
    slot = require(catalogo.slot(db, data.horario_id, service.administrador_id, lock=True),
        'Horário não encontrado para este serviço.')
    assert_available(db, slot, service.duracao_minutos)
    record = Agendamento(**data.model_dump(), status='pendente',
        preco_solicitado=service.preco, duracao_minutos_solicitada=service.duracao_minutos)
    db.add(record)
    db.flush()
    return record


TRANSITIONS = {'pendente': {'aprovado', 'recusado', 'cancelado'},
    'aprovado': {'cancelado'}, 'recusado': set(), 'cancelado': set()}


def change_status(db, owner, booking_id, target):
    record = require(db.scalar(select(Agendamento).join(Servico).where(
        Agendamento.id == booking_id, Servico.administrador_id == owner
    ).with_for_update(of=Agendamento)))
    if target not in TRANSITIONS[record.status]:
        raise HTTPException(409, 'A solicitação já foi alterada ou não permite esta transição.')
    record.status = target
    db.flush()
    return record


def bookings_query(owner):
    return select(Agendamento, Servico.nome, HorarioDisponivel.inicio, HorarioDisponivel.fim).join(
        Servico, Agendamento.servico_id == Servico.id).join(
        HorarioDisponivel, Agendamento.horario_id == HorarioDisponivel.id
    ).where(Servico.administrador_id == owner)


def booking_output(row):
    record, name, start, end = row
    return {**{column.name: getattr(record, column.name) for column in Agendamento.__table__.columns},
        'servico_nome': name, 'inicio': start, 'fim': end}
