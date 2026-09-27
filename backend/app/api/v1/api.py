from fastapi import APIRouter
from app.core.config import settings
from app.db.connection import verify_database_connection

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
        "environment": settings.ENVIRONMENT,
    }


@api_router.get("/health/db", summary="Database Health Check")
def check_db_health():
    """
    Verifies database connectivity without exposing sensitive credentials.
    """
    db_status = verify_database_connection()
    return {
        "status": "healthy" if db_status.get("postgres_connected") else "unconnected",
        "database": db_status,
    }
