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
    These dimensions are set by the Team Lead and represent qualitative areas of review,
    NOT automated scoring axes.
    """
    __tablename__ = "evaluation_criteria"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    criterion_name = Column(String(255), unique=True, nullable=False)
    criterion_description = Column(Text, nullable=True)
    weight = Column(Numeric(5, 2), nullable=True)  # Optional advisory weight; never used for auto-ranking
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Evaluation(Base):
    """
    E-12: Evaluation
    One Reviewer's structured qualitative assessment of a single Application.
    Records the strength of submitted evidence across standard dimensions,
    plus reviewer observations (strengths, concerns) and an overall recommendation.
    ARTS does NOT automatically derive a total score or ranking from evaluations.
    """
    __tablename__ = "evaluations"
    __table_args__ = (
        UniqueConstraint("application_id", "reviewer_id", name="uq_application_reviewer"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    # Reviewer-authored qualitative fields (NOT derived automatically)
    overall_recommendation = Column(String(50), nullable=True)
    overall_comments = Column(Text, nullable=True)
    strengths = Column(Text, nullable=True)   # Key strengths observed by reviewer
    concerns = Column(Text, nullable=True)    # Key concerns or open questions from reviewer
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
    The reviewer's qualitative assessment of submitted evidence strength for one criterion
    within one Evaluation. Uses qualitative ratings (not mandatory numeric scores) in line
    with the approved Evaluation & Decision-Support Framework.
    """
    __tablename__ = "evaluation_scores"
    __table_args__ = (
        UniqueConstraint("evaluation_id", "criterion_id", name="uq_evaluation_criterion"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    evaluation_id = Column(UUID(as_uuid=True), ForeignKey("evaluations.id", ondelete="CASCADE"), nullable=False, index=True)
    criterion_id = Column(UUID(as_uuid=True), ForeignKey("evaluation_criteria.id", ondelete="RESTRICT"), nullable=False, index=True)
    # Qualitative rating is the primary field; score_value is optional for future use
    qualitative_rating = Column(String(100), nullable=True)  # e.g. "Strong Evidence", "Some Evidence"
    score_value = Column(Numeric(4, 2), nullable=True)        # Optional numeric; NOT used for auto-ranking
    score_comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    evaluation = relationship("Evaluation", back_populates="scores")
    criterion = relationship("EvaluationCriterion")