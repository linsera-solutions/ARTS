from typing import List, Optional
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.evaluation import Evaluation, EvaluationScore, EvaluationCriterion
from app.schemas.evaluation import EvaluationCreate, EvaluationUpdate
from app.models.enums import EvaluationStatus
from app.services.base import BaseService
from app.core.exceptions import ConflictException, BadRequestException


class EvaluationService(BaseService[Evaluation]):
    def __init__(self):
        super().__init__(Evaluation)

    def list_by_application(self, db: Session, application_id: UUID) -> List[Evaluation]:
        return db.query(Evaluation).filter(Evaluation.application_id == application_id).all()

    def create_evaluation(self, db: Session, data: EvaluationCreate) -> Evaluation:
        existing = db.query(Evaluation).filter(
            Evaluation.application_id == data.application_id,
            Evaluation.reviewer_id == data.reviewer_id,
        ).first()
        if existing:
            raise ConflictException("An evaluation by this reviewer for this application already exists.")

        submission_date = datetime.now(timezone.utc) if data.evaluation_status == EvaluationStatus.SUBMITTED else None

        evaluation = Evaluation(
            application_id=data.application_id,
            reviewer_id=data.reviewer_id,
            overall_recommendation=data.overall_recommendation.value if data.overall_recommendation else None,
            overall_comments=data.overall_comments,
            evaluation_status=data.evaluation_status.value,
            submission_date=submission_date,
        )
        db.add(evaluation)
        db.flush()

        if data.scores:
            for s_in in data.scores:
                score = EvaluationScore(
                    evaluation_id=evaluation.id,
                    criterion_id=s_in.criterion_id,
                    score_value=s_in.score_value,
                    score_comment=s_in.score_comment,
                )
                db.add(score)

        db.commit()
        db.refresh(evaluation)
        return evaluation

    def update_evaluation(self, db: Session, id: UUID, data: EvaluationUpdate) -> Evaluation:
        evaluation = self.get(db, id)
        update_data = data.model_dump(exclude_unset=True)

        if "evaluation_status" in update_data and update_data["evaluation_status"] is not None:
            new_status = update_data["evaluation_status"]
            if new_status == EvaluationStatus.SUBMITTED and evaluation.evaluation_status != EvaluationStatus.SUBMITTED.value:
                evaluation.submission_date = datetime.now(timezone.utc)
            evaluation.evaluation_status = new_status.value

        if "overall_recommendation" in update_data:
            rec = update_data["overall_recommendation"]
            evaluation.overall_recommendation = rec.value if rec else None

        if "overall_comments" in update_data:
            evaluation.overall_comments = update_data["overall_comments"]

        if "scores" in update_data and update_data["scores"] is not None:
            # Replace scores
            db.query(EvaluationScore).filter(EvaluationScore.evaluation_id == evaluation.id).delete()
            for s_in in update_data["scores"]:
                score = EvaluationScore(
                    evaluation_id=evaluation.id,
                    criterion_id=s_in["criterion_id"],
                    score_value=s_in["score_value"],
                    score_comment=s_in.get("score_comment"),
                )
                db.add(score)

        db.commit()
        db.refresh(evaluation)
        return evaluation


evaluation_service = EvaluationService()
