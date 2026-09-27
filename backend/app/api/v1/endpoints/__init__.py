from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.roles import router as roles_router
from app.api.v1.endpoints.applicants import router as applicants_router
from app.api.v1.endpoints.applications import router as applications_router
from app.api.v1.endpoints.evaluations import router as evaluations_router
from app.api.v1.endpoints.interviews import router as interviews_router
from app.api.v1.endpoints.notes import router as notes_router

__all__ = [
    "health_router",
    "roles_router",
    "applicants_router",
    "applications_router",
    "evaluations_router",
    "interviews_router",
    "notes_router",
]
