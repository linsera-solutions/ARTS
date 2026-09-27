import uuid
from sqlalchemy import Column, String, Text, Boolean, DateTime, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base
from app.models.enums import EvaluationStatus


class EvaluationCriterion(Base):
    """
    E-11: Evaluation Criterion
    Reference entity defining a standardized dimension against which Applications are assessed.
    """
    __tablename__ = "evaluation_criteria"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    criterion_name = Column(String(255), unique=True, nullable=False)
    criterion_description = Column(Text, nullable=True)
    weight = Column(Numeric(5, 2), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Evaluation(Base):
    """
    E-12: Evaluation
    One Reviewer's structured assessment of a single Application,
    comprising an overall recommendation and per-criterion scores.
    """
    __tablename__ = "evaluations"
    __table_args__ = (
        UniqueConstraint("application_id", "reviewer_id", name="uq_application_reviewer"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    overall_recommendation = Column(String(50), nullable=True)
    overall_comments = Column(Text, nullable=True)
    evaluation_status = Column(String(50), nullable=False, default=EvaluationStatus.DRAFT.value)
    submission_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    application = relationship("Application", back_populates="evaluations")
    reviewer = relationship("User")
    scores = relationship("EvaluationScore", back_populates="evaluation", cascade="all, delete-orphan")


class EvaluationScore(Base):
    """
    E-13: Evaluation Score
    The specific score a Reviewer assigned to one Evaluation Criterion within one Evaluation.
    """
    __tablename__ = "evaluation_scores"
    __table_args__ = (
        UniqueConstraint("evaluation_id", "criterion_id", name="uq_evaluation_criterion"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id = Column(UUID(as_uuid=True), ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    criterion_id = Column(UUID(as_uuid=True), ForeignKey("evaluation_criteria.id", ondelete="RESTRICT"), nullable=False, index=True)
    score_value = Column(Numeric(4, 2), nullable=False)
    score_comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    evaluation = relationship("Evaluation", back_populates="scores")
    criterion = relationship("EvaluationCriterion")
