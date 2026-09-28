from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from pydantic import Field, model_validator
from app.schemas.common import BaseSchema
from app.models.enums import EvaluationStatus, EvaluationRecommendation

# Approved qualitative rating labels from the Evaluation & Decision-Support Framework.
# These replace mandatory numeric scores.
QUALITATIVE_RATING_VALUES = [
    "Strong Evidence",
    "Some Evidence",
    "Limited Evidence",
    "Insufficient Evidence",
    "Not Applicable",
]


class EvaluationCriterionBase(BaseSchema):
    criterion_name: str = Field(..., max_length=255)
    criterion_description: Optional[str] = None
    weight: Optional[Decimal] = None
    is_active: bool = True


class EvaluationCriterionRead(EvaluationCriterionBase):
    id: UUID
    created_at: datetime


class EvaluationScoreBase(BaseSchema):
    criterion_id: UUID
    # Qualitative rating is the primary assessment field (no mandatory numeric score)
    qualitative_rating: Optional[str] = Field(
        None,
        description="Approved qualitative rating: Strong Evidence / Some Evidence / Limited Evidence / Insufficient Evidence / Not Applicable",
    )
    # score_value is optional — not used for automated ranking
    score_value: Optional[Decimal] = Field(None, ge=0, le=100)
    score_comment: Optional[str] = None


class EvaluationScoreCreate(EvaluationScoreBase):
    pass


class EvaluationScoreRead(EvaluationScoreBase):
    id: UUID
    evaluation_id: UUID
    criterion: Optional[EvaluationCriterionRead] = None


class EvaluationBase(BaseSchema):
    application_id: UUID
    # Reviewer-authored fields — not derived automatically by ARTS
    overall_recommendation: Optional[EvaluationRecommendation] = Field(
        None,
        description="Reviewer recommendation: Advance / Needs Discussion / Waitlist / Reject. Set by reviewer, never by ARTS automatically.",
    )
    overall_comments: Optional[str] = Field(
        None,
        description="Reviewer qualitative synthesis and rationale supporting the recommendation.",
    )
    strengths: Optional[str] = Field(
        None,
        description="Key strengths observed by reviewer from submitted evidence.",
    )
    concerns: Optional[str] = Field(
        None,
        description="Key concerns or open questions identified by reviewer.",
    )
    evaluation_status: EvaluationStatus = Field(default=EvaluationStatus.DRAFT)


class EvaluationCreate(EvaluationBase):
    reviewer_id: UUID
    scores: Optional[List[EvaluationScoreCreate]] = None


class EvaluationUpsert(EvaluationBase):
    """
    Create-or-update schema for the /upsert endpoint.
    If a Draft evaluation already exists for this reviewer+application, it will be updated.
    reviewer_id is optional; the backend will fall back to the first admin user if not provided.
    """
    reviewer_id: Optional[UUID] = None
    scores: Optional[List[EvaluationScoreCreate]] = None


class EvaluationUpdate(BaseSchema):
    overall_recommendation: Optional[EvaluationRecommendation] = None
    overall_comments: Optional[str] = None
    strengths: Optional[str] = None
    concerns: Optional[str] = None
    evaluation_status: Optional[EvaluationStatus] = None
    scores: Optional[List[EvaluationScoreCreate]] = None


class EvaluationRead(EvaluationBase):
    id: UUID
    reviewer_id: UUID
    submission_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    scores: List[EvaluationScoreRead] = []