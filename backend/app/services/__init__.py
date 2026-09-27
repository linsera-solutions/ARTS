from app.services.base import BaseService
from app.services.role_service import role_service, RoleService
from app.services.applicant_service import applicant_service, ApplicantService
from app.services.application_service import application_service, ApplicationService
from app.services.evaluation_service import evaluation_service, EvaluationService
from app.services.interview_service import interview_service, InterviewService
from app.services.note_service import note_service, NoteService

__all__ = [
    "BaseService",
    "role_service",
    "RoleService",
    "applicant_service",
    "ApplicantService",
    "application_service",
    "ApplicationService",
    "evaluation_service",
    "EvaluationService",
    "interview_service",
    "InterviewService",
    "note_service",
    "NoteService",
]
