import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.enums import InterviewStatus

# Many-to-Many association table between Interview and User (Participants)
interview_participants = Table(
    "interview_participants",
    Base.metadata,
    Column("interview_id", UUID(as_uuid=True), ForeignKey("interviews.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
)


class Interview(Base):
    """
    E-15: Interview / Discussion
    A scheduled or completed discussion concerning one Application,
    including participants and outcome summary.
    """
    __tablename__ = "interviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    format = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False, default=InterviewStatus.SCHEDULED.value)
    outcome_summary = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    application = relationship("Application", back_populates="interviews")
    participants = relationship("User", secondary=interview_participants)
