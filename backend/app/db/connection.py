import logging
from typing import Dict, Any
from sqlalchemy import text
from app.core.config import settings
from app.db.session import engine
from app.db.supabase import get_supabase_client

logger = logging.getLogger(__name__)


def verify_database_connection() -> Dict[str, Any]:
    """
    Verifies connectivity to the configured PostgreSQL database and Supabase services.
    Ensures zero exposure of passwords, tokens, or sensitive credentials in reports.
    """
    result = {
        "postgres_configured": bool(settings.DATABASE_URL),
        "postgres_connected": False,
        "supabase_configured": bool(settings.SUPABASE_URL and (settings.SUPABASE_KEY or settings.SUPABASE_SERVICE_ROLE_KEY)),
        "supabase_client_ready": False,
        "message": "",
    }

    # 1. Verify PostgreSQL connection via SQLAlchemy
    if engine is not None:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            result["postgres_connected"] = True
        except Exception as e:
            logger.warning(f"PostgreSQL connection verification failed: {type(e).__name__}")
            result["postgres_connected"] = False
            result["postgres_error"] = f"Connection failed: {type(e).__name__}"
    elif settings.DATABASE_URL:
        result["postgres_error"] = "Database engine not initialized (check URI format)"
    else:
        result["postgres_error"] = "DATABASE_URL not configured"

    # 2. Verify Supabase client readiness
    supabase_client = get_supabase_client()
    if supabase_client is not None:
        result["supabase_client_ready"] = True
    elif result["supabase_configured"]:
        result["supabase_error"] = "Supabase client initialization failed"
    else:
        result["supabase_error"] = "SUPABASE_URL / SUPABASE_KEY not configured"

    # 3. Formulate human-readable message
    if result["postgres_connected"]:
        result["message"] = "PostgreSQL database successfully connected."
    elif result["postgres_configured"]:
        result["message"] = "PostgreSQL is configured but failed to connect."
    else:
        result["message"] = "Database credentials not yet configured in environment."

    return result
