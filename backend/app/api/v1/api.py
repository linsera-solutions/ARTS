from fastapi import APIRouter
from app.core.config import settings

api_router = APIRouter()


@api_router.get("/status", summary="Service Status")
def get_status():
    """
    Returns the basic health/service status of the ARTS backend API.
    """
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }
