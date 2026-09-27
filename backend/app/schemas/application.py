from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import Field
from app.schemas.common import BaseSchema
from app.models.enums import ApplicationStatus
from app.schemas.role import RoleRead
from app.schemas.applicant import ApplicantRead


class ApplicationStatusHistoryRead(BaseSchema):
    id: UUID
    application_id: UUID
    previous_status: Optional[ApplicationStatus] = None
    new_status: ApplicationStatus
    changed_by_id: Optional[UUID] = None
    reason: Optional[str] = None
    changed_at: datetime


class ApplicationBase(BaseSchema):
    role_id: UUID
    motivation_statement: Optional[str] = None
    availability_info: Optional[str] = None


class ApplicationCreate(ApplicationBase):
    applicant_id: UUID


class ApplicationStatusUpdate(BaseSchema):
    new_status: ApplicationStatus = Field(..., description="Target application lifecycle status")
    reason: Optional[str] = Field(None, description="Reason or justification for the status change")
    changed_by_id: Optional[UUID] = None


class ApplicationRead(ApplicationBase):
    id: UUID
    applicant_id: UUID
    current_status: ApplicationStatus
    submission_date: datetime
    last_updated_date: datetime
    created_at: datetime
    updated_at: datetime
    role: Optional[RoleRead] = None
    applicant: Optional[ApplicantRead] = None
    status_history: List[ApplicationStatusHistoryRead] = []
