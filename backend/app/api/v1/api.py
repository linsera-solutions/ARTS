from fastapi import APIRouter, Depends
from app.core.deps import get_current_user
from app.api.v1.endpoints import (
    auth_router,
    health_router,
    roles_router,
    applicants_router,
    applications_router,
    evaluations_router,
    interviews_router,
    notes_router,
    intake_router,
    teams_router,
)

api_router = APIRouter()

# Public Endpoints
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(health_router, prefix="/health", tags=["Health"])
api_router.include_router(intake_router, prefix="/intake", tags=["Google Intake"])

# Protected Recruiter / Candidate Review Endpoints (Enforces Authenticated Recruiter Access)
api_router.include_router(
    roles_router,
    prefix="/roles",
    tags=["Roles"],
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    applicants_router,
    prefix="/applicants",
    tags=["Applicants"],
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    applications_router,
    prefix="/applications",
    tags=["Applications"],
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    evaluations_router,
    prefix="/evaluations",
    tags=["Evaluations"],
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    interviews_router,
    prefix="/interviews",
    tags=["Interviews"],
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    notes_router,
    prefix="/notes",
    tags=["Notes"],
    dependencies=[Depends(get_current_user)],
)
api_router.include_router(
    teams_router,
    prefix="/teams",
    tags=["Teams & Roster"],
    dependencies=[Depends(get_current_user)],
)