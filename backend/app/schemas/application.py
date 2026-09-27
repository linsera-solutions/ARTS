from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID
from pydantic import EmailStr, Field, model_validator
from app.schemas.common import BaseSchema
from app.models.enums import ApplicationStatus, ProficiencyLevel
from app.schemas.role import RoleRead
from app.schemas.applicant import ApplicantRead, ExperienceCreate, PortfolioItemCreate


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
    reason: Optional[str] = Field(None, description="Human decision rationale or justification for the status change")
    changed_by_id: Optional[UUID] = None


class IntakeSkillItem(BaseSchema):
    skill_name: str = Field(..., min_length=1)
    proficiency_level: Optional[ProficiencyLevel] = None
    years_of_experience: Optional[float] = None


class IntakeEvidenceItem(BaseSchema):
    title: str = Field(..., min_length=1, description="Label or category (e.g. GitHub, Portfolio)")
    reference_link: Optional[str] = None
    attachment_reference: Optional[str] = None
    description: Optional[str] = None


class ApplicationIntakeRequest(BaseSchema):
    """
    Intake schema directly mapping Google Forms submission fields.
    """
    # Candidate Core Fields (FR-007)
    full_name: str = Field(..., min_length=1, max_length=255, description="Full Name of candidate")
    email: EmailStr = Field(..., description="Email address for candidate identity matching (FR-005)")
    phone_number: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255, description="Location / Region")
    external_profile_link: Optional[str] = Field(None, description="LinkedIn / personal portfolio URL")

    # Role Applied For
    role_name: Optional[str] = Field(None, description="Name of the target role (or use role_id)")
    role_id: Optional[UUID] = Field(None, description="Direct UUID of target role")

    # Application Fields
    motivation_statement: Optional[str] = Field(None, description="Why candidate wants to join this project")
    availability_info: Optional[str] = Field(None, description="Availability commitments during challenge")

    # Evidence, Experience & Skills
    skills: Optional[List[IntakeSkillItem]] = None
    evidence_links: Optional[List[IntakeEvidenceItem]] = None
    experiences: Optional[List[ExperienceCreate]] = None

    @model_validator(mode="after")
    def validate_role_identifier(self):
        if not self.role_name and not self.role_id:
            raise ValueError("Either role_name or role_id must be provided to identify the target position.")
        return self


class ApplicationBatchIntakeRequest(BaseSchema):
    """
    Batch intake schema for importing multiple Google Forms responses (FR-002).
    """
    submissions: List[ApplicationIntakeRequest] = Field(..., min_length=1)


class IntakeResultItem(BaseSchema):
    email: str
    full_name: str
    application_id: Optional[UUID] = None
    applicant_id: Optional[UUID] = None
    role_name: Optional[str] = None
    status: str  # created, updated, rejected
    reason: Optional[str] = None


class IntakeSummaryResponse(BaseSchema):
    total_received: int
    accepted: int
    updated: int
    rejected: int
    results: List[IntakeResultItem]
    errors: List[str] = []


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


class ApplicationDetailRead(ApplicationRead):
    """
    Consolidated aggregate profile combining record data, skills, experience,
    availability, evidence links, evaluations, notes, and status (FR-011).
    """
    evaluations: List[Any] = []
    interviews: List[Any] = []
    notes: List[Any] = []
