from typing import Optional, List
from datetime import datetime
from uuid import UUID
from pydantic import Field
from app.schemas.common import BaseSchema
from app.models.enums import RoleStatus


class SkillBase(BaseSchema):
    skill_name: str
    skill_category: Optional[str] = None
    is_active: bool = True


class SkillRead(SkillBase):
    id: UUID
    created_at: datetime


class RoleBase(BaseSchema):
    role_name: str = Field(..., max_length=255, description="Name of the team role")
    role_description: Optional[str] = None
    number_of_openings: int = Field(default=1, ge=0, description="Available openings count")
    role_status: RoleStatus = Field(default=RoleStatus.OPEN, description="Current role status")
    application_deadline: Optional[datetime] = None


class RoleCreate(RoleBase):
    team_id: Optional[UUID] = None
    desired_skill_ids: Optional[List[UUID]] = None


class RoleUpdate(BaseSchema):
    role_name: Optional[str] = Field(None, max_length=255)
    role_description: Optional[str] = None
    number_of_openings: Optional[int] = Field(None, ge=0)
    role_status: Optional[RoleStatus] = None
    application_deadline: Optional[datetime] = None
    team_id: Optional[UUID] = None


class RoleRead(RoleBase):
    id: UUID
    team_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    desired_skills: List[SkillRead] = []
