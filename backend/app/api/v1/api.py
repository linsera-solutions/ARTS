from fastapi import APIRouter
from app.api.v1.endpoints import (
    health_router,
    roles_router,
    applicants_router,
    applications_router,
    evaluations_router,
    interviews_router,
    notes_router,
)

api_router = APIRouter()

api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(roles_router, prefix="/roles", tags=["Roles"])
api_router.include_router(applicants_router, prefix="/applicants", tags=["Applicants"])
api_router.include_router(applications_router, prefix="/applications", tags=["Applications"])
api_router.include_router(evaluations_router, prefix="/evaluations", tags=["Evaluations"])
api_router.include_router(interviews_router, prefix="/interviews", tags=["Interviews"])
api_router.include_router(notes_router, prefix="/notes", tags=["Notes"])
