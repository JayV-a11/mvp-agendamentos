from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request
from sqlalchemy import select

from app.api.dependencies import DB, Auth
from app.models import Servico
from app.repositories import catalogo
from app.schemas.domain import ServiceInput, ServiceOutput, SlotOutput
from app.services import agenda

public = APIRouter(prefix='/publico', tags=['Catálogo público'])
admin = APIRouter(prefix='/admin/servicos', tags=['Serviços administrativos'])
Limit = Annotated[int, Query(ge=1, le=100)]
Offset = Annotated[int, Query(ge=0)]


@public.get('/configuracao')
def public_config(request: Request):
    return {'fuso_horario': request.app.state.settings.business_timezone}


@public.get('/servicos', response_model=list[ServiceOutput])
def public_services(db: DB, limite: Limit = 100, inicio: Offset = 0):
    return list(db.scalars(select(Servico).where(Servico.ativo.is_(True)).order_by(
        Servico.nome, Servico.id).offset(inicio).limit(limite)))


@public.get('/servicos/{service_id}', response_model=ServiceOutput)
def public_service(service_id: UUID, db: DB):
    return agenda.active_service(db, service_id)


@public.get('/servicos/{service_id}/horarios', response_model=list[SlotOutput])
def public_slots(service_id: UUID, db: DB, limite: Limit = 100, inicio: Offset = 0):
    record = agenda.active_service(db, service_id)
    from app.models import HorarioDisponivel
    return list(db.scalars(catalogo.available_slots(record).order_by(
        HorarioDisponivel.inicio, HorarioDisponivel.id).offset(inicio).limit(limite)))


@admin.get('', response_model=list[ServiceOutput])
def list_services(db: DB, identity: Auth, limite: Limit = 100, inicio: Offset = 0):
    return list(db.scalars(select(Servico).where(Servico.administrador_id == identity.admin.id)
        .order_by(Servico.nome, Servico.id).offset(inicio).limit(limite)))


@admin.post('', response_model=ServiceOutput, status_code=201)
def create(data: ServiceInput, db: DB, identity: Auth):
    return agenda.create_service(db, identity.admin.id, data)


@admin.put('/{service_id}', response_model=ServiceOutput)
def update(service_id: UUID, data: ServiceInput, db: DB, identity: Auth):
    return agenda.update_service(db, identity.admin.id, service_id, data)
