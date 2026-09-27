from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.connection import verify_database_connection

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="REST API for Applicant Review & Team Selection System (ARTS) MVP",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to ARTS (Applicant Review & Team Selection System) API",
        "docs": f"{settings.API_V1_STR}/docs",
        "health": "/health",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health", tags=["Health"])
def health_check():
    db_status = verify_database_connection()
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": {
            "postgres_connected": db_status["postgres_connected"],
            "supabase_client_ready": db_status["supabase_client_ready"],
            "message": db_status["message"],
        },
    }
