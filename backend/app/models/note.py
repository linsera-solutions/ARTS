import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.enums import NoteRelatedEntityType, NoteVisibility


class Note(Base):
    """
    E-14: Note
    An informal annotation a User may attach to an Applicant or Application
    outside the formal Evaluation process.
    """
    __tablename__ = "notes"
    __table_args__ = (
        Index("idx_notes_entity", "related_entity_type", "related_entity_id"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    related_entity_type = Column(String(50), nullable=False)  # Applicant, Application
    related_entity_id = Column(UUID(as_uuid=True), nullable=False)
    note_text = Column(Text, nullable=False)
    visibility = Column(String(50), nullable=False, default=NoteVisibility.INTERNAL.value)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    author = relationship("User")
