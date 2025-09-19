from fastapi import (
    APIRouter,
    Depends
)

from app.application.services.health_service import HealthService
from app.utils.provider import get_health_service

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def health(service: HealthService = Depends(get_health_service)):
    return service.get_health()


@router.get("/env-check")
def env_check(service: HealthService = Depends(get_health_service)):
    return service.get_env_check()