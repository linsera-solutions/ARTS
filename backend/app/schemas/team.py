from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from pydantic import Field
from app.schemas.common import BaseSchema
from app.models.enums import TeamStatus, MembershipStatus, RoleStatus
from app.schemas.role import RoleRead
from app.schemas.applicant import ApplicantRead


class TeamBase(BaseSchema):
    team_name: str = Field(..., max_length=255)
    team_description: Optional[str] = None
    team_status: TeamStatus = Field(default=TeamStatus.FORMING)


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseSchema):
    team_name: Optional[str] = Field(None, max_length=255)
    team_description: Optional[str] = None
    team_status: Optional[TeamStatus] = None


class TeamMemberBase(BaseSchema):
    team_id: UUID
    applicant_id: UUID
    source_application_id: UUID
    role_id: UUID
    membership_status: MembershipStatus = Field(default=MembershipStatus.ACTIVE)


class TeamMemberAssignRequest(BaseSchema):
    """
    Request payload to assign a selected candidate to a specific team role slot.
    """
    application_id: UUID = Field(..., description="ID of the candidate application (must be Selected)")
    role_id: UUID = Field(..., description="Target role slot ID to assign candidate into")


class TeamMemberReassignRequest(BaseSchema):
    """
    Request payload to reassign an active team member to a different role slot.
    """
    target_role_id: UUID = Field(..., description="New role slot ID to assign member into")
    reason: Optional[str] = Field(None, description="Reason for role reassignment")


class TeamMemberRead(TeamMemberBase):
    id: UUID
    join_date: date
    created_at: datetime
    updated_at: datetime
    applicant: Optional[ApplicantRead] = None
    role: Optional[RoleRead] = None


class TeamRead(TeamBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    roles: List[RoleRead] = []
    members: List[TeamMemberRead] = []


class RosterSlotRead(BaseSchema):
    """
    A single position slot in the 4-member team roster.
    """
    role_id: UUID
    role_name: str
    role_description: Optional[str] = None
    number_of_openings: int = 1
    role_status: RoleStatus = RoleStatus.OPEN
    is_filled: bool = False
    assigned_member: Optional[TeamMemberRead] = None


class UnassignedCandidateRead(BaseSchema):
    """
    A candidate in 'Selected' status who has not yet been placed into a team slot.
    """
    application_id: UUID
    applicant_id: UUID
    full_name: str
    email: str
    location: Optional[str] = None
    original_applied_role: str
    original_role_id: UUID
    skills: List[str] = []
    selection_date: datetime


class TeamOverviewResponse(BaseSchema):
    """
    Consolidated response for the Team Formation roster workspace (SCR-08).
    """
    team_id: UUID
    team_name: str
    team_description: Optional[str] = None
    team_status: TeamStatus
    total_slots: int = 4
    filled_slots_count: int = 0
    is_team_complete: bool = False
    slots: List[RosterSlotRead] = []
    unassigned_selected_candidates: List[UnassignedCandidateRead] = []