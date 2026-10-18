from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request
from pydantic import AwareDatetime
from sqlalchemy import select

from app.api.dependencies import DB, Auth
from app.api.catalogo import Limit, Offset
from app.db.session import get_engine
from app.models import Agendamento, HorarioDisponivel
from app.schemas.domain import (SlotInput, SlotOutput, BlockInput, BookingInput,
    BookingOutput, BookingConfirmation, Status, StatusInput)
from app.services import agenda
from app.services.auth import limit_requests

admin = APIRouter(prefix='/admin', tags=['Agenda administrativa'])
public = APIRouter(prefix='/publico', tags=['Solicitações públicas'])
DateFilter = Annotated[AwareDatetime | None, Query()]


@admin.get('/horarios', response_model=list[SlotOutput])
def list_slots(db: DB, identity: Auth, de: DateFilter = None, ate: DateFilter = None,
               limite: Limit = 100, inicio: Offset = 0):
    query = select(HorarioDisponivel).where(HorarioDisponivel.administrador_id == identity.admin.id)
    if de is not None:
        query = query.where(HorarioDisponivel.inicio >= de)
    if ate is not None:
        query = query.where(HorarioDisponivel.inicio < ate)
    return list(db.scalars(query.order_by(HorarioDisponivel.inicio, HorarioDisponivel.id)
        .offset(inicio).limit(limite)))


@admin.post('/horarios', response_model=SlotOutput, status_code=201)
def create_slot(data: SlotInput, db: DB, identity: Auth):
    return agenda.create_slot(db, identity.admin.id, data)


@admin.patch('/horarios/{slot_id}/bloqueio', response_model=SlotOutput)
def block(slot_id: UUID, data: BlockInput, db: DB, identity: Auth):
    return agenda.block_slot(db, identity.admin.id, slot_id, data.bloqueado)


@public.post('/agendamentos', response_model=BookingConfirmation, status_code=201)
def request_booking(data: BookingInput, request: Request, db: DB):
    ip = request.client.host if request.client else 'desconhecido'
    limit_requests(get_engine(request), request.app.state.settings, 'solicitacao-ip', ip, 20, 600)
    return agenda.request_booking(db, data)


@admin.get('/agendamentos', response_model=list[BookingOutput])
def list_bookings(db: DB, identity: Auth, status: Status | None = None,
                  de: DateFilter = None, ate: DateFilter = None,
                  limite: Limit = 100, inicio: Offset = 0):
    query = agenda.bookings_query(identity.admin.id)
    if status is not None:
        query = query.where(Agendamento.status == status)
    if de is not None:
        query = query.where(HorarioDisponivel.inicio >= de)
    if ate is not None:
        query = query.where(HorarioDisponivel.inicio < ate)
    return [agenda.booking_output(row) for row in db.execute(query.order_by(
        HorarioDisponivel.inicio, Agendamento.id).offset(inicio).limit(limite))]


@admin.patch('/agendamentos/{booking_id}/status', response_model=BookingOutput)
def status_change(booking_id: UUID, data: StatusInput, db: DB, identity: Auth):
    record = agenda.change_status(db, identity.admin.id, booking_id, data.status)
    row = db.execute(agenda.bookings_query(identity.admin.id).where(Agendamento.id == record.id)).one()
    return agenda.booking_output(row)
