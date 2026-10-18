from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Body, Request, Response

from app.api.dependencies import DB, Auth
from app.schemas.domain import ServiceOutput
from app.services import agenda, photos
from app.repositories import catalogo

router = APIRouter(tags=['Fotografias'])


@router.get('/admin/servicos/{service_id}/foto', responses={200: {'content': {'image/webp': {}}}})
def admin_download(service_id: UUID, request: Request, db: DB, identity: Auth):
    record = agenda.require(catalogo.service(db, service_id, identity.admin.id))
    if record.imagem_url is None:
        from fastapi import HTTPException
        raise HTTPException(404, 'Este serviço não possui foto cadastrada.')
    data = photos.Storage(request.app.state.settings).download(
        record.administrador_id, record.id, photos.photo_version(record.imagem_url))
    return Response(data, media_type='image/webp', headers={'Cache-Control': 'no-store'})


@router.put('/admin/servicos/{service_id}/foto', response_model=ServiceOutput)
def upload(service_id: UUID, request: Request, db: DB, identity: Auth,
    data: Annotated[bytes, Body(media_type='application/octet-stream')]):
    content_type = request.headers.get('content-type', '').split(';', 1)[0].lower()
    return photos.upload_photo(db, request.app.state.settings, identity.admin.id, service_id, data, content_type)


@router.delete('/admin/servicos/{service_id}/foto', response_model=ServiceOutput)
def delete(service_id: UUID, request: Request, db: DB, identity: Auth):
    return photos.delete_photo(db, request.app.state.settings, identity.admin.id, service_id)


@router.get('/publico/servicos/{service_id}/foto', responses={200: {'content': {'image/webp': {}}}})
def download(service_id: UUID, request: Request, db: DB):
    record = agenda.active_service(db, service_id)
    if record.imagem_url is None:
        from fastapi import HTTPException
        raise HTTPException(404, 'Este serviço não possui foto cadastrada.')
    data = photos.Storage(request.app.state.settings).download(
        record.administrador_id, record.id, photos.photo_version(record.imagem_url))
    return Response(data, media_type='image/webp', headers={'Cache-Control': 'public, max-age=60'})
