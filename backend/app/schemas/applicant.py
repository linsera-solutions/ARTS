from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal
from pydantic import EmailStr, Field, HttpUrl, model_validator
from app.schemas.common import BaseSchema
from app.models.enums import ApplicantStatus, ProficiencyLevel
from app.schemas.role import SkillRead


class ExperienceBase(BaseSchema):
    title: str = Field(..., max_length=255, description="Role title or position held")
    organization: Optional[str] = Field(None, max_length=255, description="Organization, company, or project name")
    start_date: date = Field(..., description="Start date of experience")
    end_date: Optional[date] = Field(None, description="End date (blank if ongoing)")
    description: Optional[str] = Field(None, description="Description of contributions and technologies")

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be earlier than start_date")
        return self


class ExperienceCreate(ExperienceBase):
    pass


class ExperienceRead(ExperienceBase):
    id: UUID
    applicant_id: UUID
    created_at: datetime


class PortfolioItemBase(BaseSchema):
    title: str = Field(..., max_length=255, description="Title or descriptive label of the evidence/work sample")
    description: Optional[str] = Field(None, description="Explanation or context of the work sample")
    reference_link: Optional[str] = Field(None, description="External URL to repo, portfolio, live app, or video")
    attachment_reference: Optional[str] = Field(None, description="Uploaded file reference or storage ID")

    @model_validator(mode="after")
    def validate_evidence_present(self):
        if not self.reference_link and not self.attachment_reference:
            raise ValueError("At least one of reference_link or attachment_reference must be provided.")
        return self


class PortfolioItemCreate(PortfolioItemBase):
    pass


class PortfolioItemRead(PortfolioItemBase):
    id: UUID
    applicant_id: UUID
    date_added: datetime
    created_at: datetime


class EvidenceLinkCreate(BaseSchema):
    title: str = Field(..., min_length=1, max_length=255, description="Descriptive label (e.g. GitHub, Figma, Demo Video)")
    reference_link: str = Field(..., description="Well-formed URL (FR-018)")
    description: Optional[str] = None


class ApplicantSkillBase(BaseSchema):
    skill_id: UUID
    proficiency_level: Optional[ProficiencyLevel] = None
    years_of_experience: Optional[Decimal] = Field(None, ge=0, decimal_places=1)


class ApplicantSkillCreate(ApplicantSkillBase):
    pass


class ApplicantSkillRead(ApplicantSkillBase):
    id: UUID
    applicant_id: UUID
    skill: Optional[SkillRead] = None


class ApplicantBase(BaseSchema):
    full_name: str = Field(..., min_length=1, max_length=255, description="Candidate full name")
    email: EmailStr = Field(..., description="Primary contact and unique identifier for candidate matching")
    phone_number: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255, description="Geographic location / timezone")
    external_profile_link: Optional[str] = Field(None, description="LinkedIn, personal website, or primary profile URL")
    applicant_status: ApplicantStatus = Field(default=ApplicantStatus.ACTIVE)


class ApplicantCreate(ApplicantBase):
    experiences: Optional[List[ExperienceCreate]] = None
    portfolio_items: Optional[List[PortfolioItemCreate]] = None
    skills: Optional[List[ApplicantSkillCreate]] = None


class ApplicantUpdate(BaseSchema):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    external_profile_link: Optional[str] = None
    applicant_status: Optional[ApplicantStatus] = None


class ApplicantRead(ApplicantBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    experiences: List[ExperienceRead] = []
    portfolio_items: List[PortfolioItemRead] = []
    applicant_skills: List[ApplicantSkillRead] = []
