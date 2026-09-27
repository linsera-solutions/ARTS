from fastapi import APIRouter
from app.core.config import settings
from app.db.connection import verify_database_connection
from app.schemas.common import HealthCheckResponse, DatabaseHealthStatus

router = APIRouter()


@router.get("", response_model=HealthCheckResponse, summary="Service & Database Health")
def get_health():
    """
    Returns application and database readiness status without exposing sensitive credentials.
    """
    db_status = verify_database_connection()
    return HealthCheckResponse(
        status="healthy",
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
        database=DatabaseHealthStatus(
            postgres_connected=db_status["postgres_connected"],
            supabase_client_ready=db_status["supabase_client_ready"],
            message=db_status["message"],
        ),
    )
