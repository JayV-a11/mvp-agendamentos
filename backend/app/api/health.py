from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(tags=["Saúde"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Verifica se a API responde",
    description="Verifica apenas a aplicação HTTP. Não consulta banco ou serviços externos.",
)
def health() -> HealthResponse:
    return HealthResponse()
