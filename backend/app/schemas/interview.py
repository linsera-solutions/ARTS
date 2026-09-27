from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import Field
from app.schemas.common import BaseSchema
from app.models.enums import InterviewStatus


class InterviewBase(BaseSchema):
    application_id: UUID
    scheduled_at: datetime
    format: Optional[str] = Field(None, max_length=100)
    status: InterviewStatus = Field(default=InterviewStatus.SCHEDULED)
    outcome_summary: Optional[str] = None


class InterviewCreate(InterviewBase):
    participant_user_ids: Optional[List[UUID]] = None


class InterviewUpdate(BaseSchema):
    scheduled_at: Optional[datetime] = None
    format: Optional[str] = Field(None, max_length=100)
    status: Optional[InterviewStatus] = None
    outcome_summary: Optional[str] = None
    participant_user_ids: Optional[List[UUID]] = None


class InterviewRead(InterviewBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
