import uuid
from sqlalchemy import Column, String, Text, Integer, Date, DateTime, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.enums import RoleStatus, TeamStatus, MembershipStatus

# Many-to-Many association table between Role and Skill
role_skills = Table(
    "role_skills",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", UUID(as_uuid=True), ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class Team(Base):
    """
    E-05: Team
    A group that Applicants are ultimately selected into upon successful completion of review.
    """
    __tablename__ = "teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_name = Column(String(255), unique=True, nullable=False)
    team_description = Column(Text, nullable=True)
    team_status = Column(String(50), nullable=False, default=TeamStatus.FORMING.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    roles = relationship("Role", back_populates="team", cascade="all, delete-orphan")
    members = relationship("TeamMember", back_populates="team")


class Role(Base):
    """
    E-04: Role
    A defined position or opportunity that a Team is recruiting for,
    and that Applications are submitted against.
    """
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="SET NULL"), nullable=True, index=True)
    role_name = Column(String(255), nullable=False)
    role_description = Column(Text, nullable=True)
    number_of_openings = Column(Integer, nullable=False, default=1)
    role_status = Column(String(50), nullable=False, default=RoleStatus.OPEN.value)
    application_deadline = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    team = relationship("Team", back_populates="roles")
    applications = relationship("Application", back_populates="role")
    desired_skills = relationship("Skill", secondary=role_skills)
    team_members = relationship("TeamMember", back_populates="role")


class TeamMember(Base):
    """
    E-06: Team Member
    The confirmed assignment of a selected Applicant to a Team and Role,
    linking the review outcome to the roster.
    """
    __tablename__ = "team_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="RESTRICT"), nullable=False, index=True)
    applicant_id = Column(UUID(as_uuid=True), ForeignKey("applicants.id", ondelete="RESTRICT"), nullable=False, index=True)
    source_application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="RESTRICT"), nullable=False, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False, index=True)
    join_date = Column(Date, nullable=False, server_default=func.current_date())
    membership_status = Column(String(50), nullable=False, default=MembershipStatus.ACTIVE.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    team = relationship("Team", back_populates="members")
    applicant = relationship("Applicant")
    source_application = relationship("Application")
    role = relationship("Role", back_populates="team_members")
