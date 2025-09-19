from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from fastapi.responses import RedirectResponse

from app.application.services.auth_service import AuthService
from app.utils.provider import get_auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
def login(service: AuthService = Depends(get_auth_service)):
    return RedirectResponse(service.authorize_url())


@router.get("/callback")
def callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    service: AuthService = Depends(get_auth_service)
):
    if error:
        raise HTTPException(status_code=400, detail={"oauth_error": error, "description": error_description})

    if not code:
        raise HTTPException(status_code=400, detail="Missing 'code' param.")
    
    return service.handle_callback(code)


@router.get("/status")
def auth_status(service: AuthService = Depends(get_auth_service)):
    return service.status()
