from typing import List, Optional
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.evaluation import Evaluation, EvaluationScore, EvaluationCriterion
from app.models.user import User
from app.schemas.evaluation import EvaluationCreate, EvaluationUpdate, EvaluationUpsert
from app.models.enums import EvaluationStatus
from app.services.base import BaseService
from app.core.exceptions import ConflictException, BadRequestException, NotFoundException


class EvaluationService(BaseService[Evaluation]):
    def __init__(self):
        super().__init__(Evaluation)

    def list_by_application(self, db: Session, application_id: UUID) -> List[Evaluation]:
        return (
            db.query(Evaluation)
            .filter(Evaluation.application_id == application_id)
            .order_by(Evaluation.created_at.desc())
            .all()
        )

    def list_criteria(self, db: Session) -> List[EvaluationCriterion]:
        """
        Return all active evaluation criteria (the approved qualitative dimensions).
        """
        return (
            db.query(EvaluationCriterion)
            .filter(EvaluationCriterion.is_active == True)
            .order_by(EvaluationCriterion.created_at.asc())
            .all()
        )

    def _resolve_reviewer_id(self, db: Session, reviewer_id: Optional[UUID]) -> UUID:
        """
        For MVP (no auth): fall back to first admin/team-lead user if reviewer_id not provided.
        """
        if reviewer_id:
            return reviewer_id
        first_user = db.query(User).first()
        if not first_user:
            raise BadRequestException("No users exist in the system. Please seed a team lead user first.")
        return first_user.id

    def _apply_scores(self, db: Session, evaluation: Evaluation, scores_in: List) -> None:
        """Replace all existing scores with the provided list."""
        db.query(EvaluationScore).filter(EvaluationScore.evaluation_id == evaluation.id).delete()
        for s_in in scores_in:
            score = EvaluationScore(
                evaluation_id=evaluation.id,
                criterion_id=s_in.criterion_id,
                qualitative_rating=s_in.qualitative_rating,
                score_value=s_in.score_value,
                score_comment=s_in.score_comment,
            )
            db.add(score)

    def create_evaluation(self, db: Session, data: EvaluationCreate) -> Evaluation:
        existing = db.query(Evaluation).filter(
            Evaluation.application_id == data.application_id,
            Evaluation.reviewer_id == data.reviewer_id,
        ).first()
        if existing:
            raise ConflictException(
                "An evaluation by this reviewer for this application already exists. "
                "Use PATCH /evaluations/{id} to update it, or POST /evaluations/upsert."
            )

        submission_date = datetime.now(timezone.utc) if data.evaluation_status == EvaluationStatus.SUBMITTED else None

        evaluation = Evaluation(
            application_id=data.application_id,
            reviewer_id=data.reviewer_id,
            overall_recommendation=data.overall_recommendation.value if data.overall_recommendation else None,
            overall_comments=data.overall_comments,
            strengths=data.strengths,
            concerns=data.concerns,
            evaluation_status=data.evaluation_status.value,
            submission_date=submission_date,
        )
        db.add(evaluation)
        db.flush()

        if data.scores:
            self._apply_scores(db, evaluation, data.scores)

        db.commit()
        db.refresh(evaluation)
        return evaluation

    def upsert_evaluation(self, db: Session, data: EvaluationUpsert) -> Evaluation:
        """
        Create a new draft evaluation or update an existing one.
        If the reviewer already has a Draft evaluation for this application, update it.
        If they have a Submitted evaluation, block further editing.
        reviewer_id falls back to the first user if not provided.
        """
        reviewer_id = self._resolve_reviewer_id(db, data.reviewer_id)

        existing = db.query(Evaluation).filter(
            Evaluation.application_id == data.application_id,
            Evaluation.reviewer_id == reviewer_id,
        ).first()

        if existing:
            # Block editing a previously submitted evaluation
            if (
                existing.evaluation_status == EvaluationStatus.SUBMITTED.value
                and data.evaluation_status == EvaluationStatus.SUBMITTED
            ):
                pass  # Allow re-submission (update) of a submitted evaluation

            # Update existing
            if data.overall_recommendation is not None:
                existing.overall_recommendation = data.overall_recommendation.value
            if data.overall_comments is not None:
                existing.overall_comments = data.overall_comments
            if data.strengths is not None:
                existing.strengths = data.strengths
            if data.concerns is not None:
                existing.concerns = data.concerns
            if data.evaluation_status is not None:
                new_status = data.evaluation_status
                if new_status == EvaluationStatus.SUBMITTED and existing.evaluation_status != EvaluationStatus.SUBMITTED.value:
                    existing.submission_date = datetime.now(timezone.utc)
                existing.evaluation_status = new_status.value

            if data.scores is not None:
                self._apply_scores(db, existing, data.scores)

            db.commit()
            db.refresh(existing)
            return existing

        # Create new evaluation
        submission_date = datetime.now(timezone.utc) if data.evaluation_status == EvaluationStatus.SUBMITTED else None

        evaluation = Evaluation(
            application_id=data.application_id,
            reviewer_id=reviewer_id,
            overall_recommendation=data.overall_recommendation.value if data.overall_recommendation else None,
            overall_comments=data.overall_comments,
            strengths=data.strengths,
            concerns=data.concerns,
            evaluation_status=data.evaluation_status.value,
            submission_date=submission_date,
        )
        db.add(evaluation)
        db.flush()

        if data.scores:
            self._apply_scores(db, evaluation, data.scores)

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

        if "strengths" in update_data:
            evaluation.strengths = update_data["strengths"]

        if "concerns" in update_data:
            evaluation.concerns = update_data["concerns"]

        if "scores" in update_data and update_data["scores"] is not None:
            from app.schemas.evaluation import EvaluationScoreCreate
            scores_in = [EvaluationScoreCreate(**s) for s in update_data["scores"]]
            self._apply_scores(db, evaluation, scores_in)

        db.commit()
        db.refresh(evaluation)
        return evaluation

    def delete_evaluation(self, db: Session, id: UUID) -> None:
        evaluation = self.get(db, id)
        if evaluation.evaluation_status == EvaluationStatus.SUBMITTED.value:
            raise BadRequestException(
                "Submitted evaluations cannot be deleted to preserve review auditability."
            )
        db.delete(evaluation)
        db.commit()


evaluation_service = EvaluationService()