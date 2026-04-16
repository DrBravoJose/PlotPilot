from fastapi import APIRouter, Depends

from interfaces.api.dependencies import get_openai_oauth_service


router = APIRouter(prefix="/auth/openai", tags=["openai-auth"])


@router.get("/status")
def get_status(service=Depends(get_openai_oauth_service)):
    return service.get_status()


@router.post("/start")
def start(service=Depends(get_openai_oauth_service)):
    return service.start_auth_flow()


@router.post("/logout")
def logout(service=Depends(get_openai_oauth_service)):
    return service.logout()
