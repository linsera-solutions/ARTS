import uuid
from sqlalchemy import Column, String, Text, Boolean, Date, DateTime, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.enums import ApplicantStatus, ProficiencyLevel


class Skill(Base):
    """
    E-07: Skill
    Controlled-vocabulary reference entity describing a discrete skill or competency.
    """
    __tablename__ = "skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_name = Column(String(150), unique=True, nullable=False, index=True)
    skill_category = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Applicant(Base):
    """
    E-02: Applicant
    Individual who submits Applications and is the subject of review and selection.
    """
    __tablename__ = "applicants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone_number = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    external_profile_link = Column(Text, nullable=True)
    applicant_status = Column(String(50), nullable=False, default=ApplicantStatus.ACTIVE.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    applications = relationship("Application", back_populates="applicant", cascade="all, delete-orphan")
    experiences = relationship("Experience", back_populates="applicant", cascade="all, delete-orphan")
    portfolio_items = relationship("PortfolioItem", back_populates="applicant", cascade="all, delete-orphan")
    applicant_skills = relationship("ApplicantSkill", back_populates="applicant", cascade="all, delete-orphan")


class ApplicantSkill(Base):
    """
    E-08: Applicant Skill
    Associative record capturing that an Applicant claims a given Skill.
    """
    __tablename__ = "applicant_skills"
    __table_args__ = (
        UniqueConstraint("applicant_id", "skill_id", name="uq_applicant_skill"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_id = Column(UUID(as_uuid=True), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id", ondelete="RESTRICT"), nullable=False, index=True)
    proficiency_level = Column(String(50), nullable=True)
    years_of_experience = Column(Numeric(4, 1), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    applicant = relationship("Applicant", back_populates="applicant_skills")
    skill = relationship("Skill")


class Experience(Base):
    """
    E-09: Experience
    A discrete prior work, project, or activity record supporting an Applicant's profile.
    """
    __tablename__ = "experiences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_id = Column(UUID(as_uuid=True), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    organization = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    applicant = relationship("Applicant", back_populates="experiences")


class PortfolioItem(Base):
    """
    E-10: Portfolio Item
    A work sample or external reference submitted by an Applicant to evidence relevant prior work.
    """
    __tablename__ = "portfolio_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    applicant_id = Column(UUID(as_uuid=True), ForeignKey("applicants.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    reference_link = Column(Text, nullable=True)
    attachment_reference = Column(Text, nullable=True)
    date_added = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    applicant = relationship("Applicant", back_populates="portfolio_items")
