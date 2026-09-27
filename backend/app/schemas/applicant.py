from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
from decimal import Decimal
from pydantic import EmailStr, Field, model_validator
from app.schemas.common import BaseSchema
from app.models.enums import ApplicantStatus, ProficiencyLevel
from app.schemas.role import SkillRead


class ExperienceBase(BaseSchema):
    title: str = Field(..., max_length=255)
    organization: Optional[str] = Field(None, max_length=255)
    start_date: date
    end_date: Optional[date] = None
    description: Optional[str] = None

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
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    reference_link: Optional[str] = None
    attachment_reference: Optional[str] = None

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
    full_name: str = Field(..., max_length=255)
    email: EmailStr
    phone_number: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    external_profile_link: Optional[str] = None
    applicant_status: ApplicantStatus = Field(default=ApplicantStatus.ACTIVE)


class ApplicantCreate(ApplicantBase):
    experiences: Optional[List[ExperienceCreate]] = None
    portfolio_items: Optional[List[PortfolioItemCreate]] = None
    skills: Optional[List[ApplicantSkillCreate]] = None


class ApplicantUpdate(BaseSchema):
    full_name: Optional[str] = Field(None, max_length=255)
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
