from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.models import Agendamento, HorarioDisponivel, Servico
from app.core.security import now

ACTIVE = ('pendente', 'aprovado')


def service(session: Session, service_id, owner=None, lock=False):
    query = select(Servico).where(Servico.id == service_id)
    if owner is not None:
        query = query.where(Servico.administrador_id == owner)
    if lock:
        query = query.with_for_update()
    return session.scalar(query)


def slot(session: Session, slot_id, owner=None, lock=False):
    query = select(HorarioDisponivel).where(HorarioDisponivel.id == slot_id)
    if owner is not None:
        query = query.where(HorarioDisponivel.administrador_id == owner)
    if lock:
        query = query.with_for_update()
    return session.scalar(query)


def occupied(session, slot_id):
    return session.scalar(select(exists().where(
        Agendamento.horario_id == slot_id, Agendamento.status.in_(ACTIVE))))


def available_slots(service_record):
    h = HorarioDisponivel
    from sqlalchemy import func
    return select(h).where(h.administrador_id == service_record.administrador_id,
        h.inicio > now(), h.bloqueado.is_(False),
        func.extract('epoch', h.fim - h.inicio) >= service_record.duracao_minutos * 60,
        ~exists().where(Agendamento.horario_id == h.id, Agendamento.status.in_(ACTIVE)))
