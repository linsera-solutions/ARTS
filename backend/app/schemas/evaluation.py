from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal
from pydantic import Field
from app.schemas.common import BaseSchema
from app.models.enums import EvaluationStatus, EvaluationRecommendation


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
    score_value: Decimal = Field(..., ge=0, le=100)
    score_comment: Optional[str] = None


class EvaluationScoreCreate(EvaluationScoreBase):
    pass


class EvaluationScoreRead(EvaluationScoreBase):
    id: UUID
    evaluation_id: UUID
    criterion: Optional[EvaluationCriterionRead] = None


class EvaluationBase(BaseSchema):
    application_id: UUID
    overall_recommendation: Optional[EvaluationRecommendation] = None
    overall_comments: Optional[str] = None
    evaluation_status: EvaluationStatus = Field(default=EvaluationStatus.DRAFT)


class EvaluationCreate(EvaluationBase):
    reviewer_id: UUID
    scores: Optional[List[EvaluationScoreCreate]] = None


class EvaluationUpdate(BaseSchema):
    overall_recommendation: Optional[EvaluationRecommendation] = None
    overall_comments: Optional[str] = None
    evaluation_status: Optional[EvaluationStatus] = None
    scores: Optional[List[EvaluationScoreCreate]] = None


class EvaluationRead(EvaluationBase):
    id: UUID
    reviewer_id: UUID
    submission_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    scores: List[EvaluationScoreRead] = []
