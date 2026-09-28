from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.evaluation import (
    EvaluationRead,
    EvaluationCreate,
    EvaluationUpdate,
    EvaluationUpsert,
    EvaluationCriterionRead,
)
from app.schemas.common import ResponseEnvelope
from app.services.evaluation_service import evaluation_service

router = APIRouter()


@router.get(
    "/criteria",
    response_model=ResponseEnvelope[List[EvaluationCriterionRead]],
    summary="List Evaluation Criteria",
    description=(
        "Returns all active qualitative evaluation dimensions seeded from the approved "
        "Evaluation & Decision-Support Framework. Used by the review form to build per-criterion "
        "assessment fields. Criteria are NOT scoring axes; they guide human evidence assessment."
    ),
)
def list_criteria(db: Session = Depends(get_db)):
    criteria = evaluation_service.list_criteria(db)
    return ResponseEnvelope(data=criteria)


@router.get(
    "",
    response_model=ResponseEnvelope[List[EvaluationRead]],
    summary="List Evaluations by Application",
)
def list_evaluations(
    application_id: UUID = Query(..., description="Application ID to fetch evaluations for"),
    db: Session = Depends(get_db),
):
    """
    Retrieve all structured evaluations and per-criterion qualitative assessments
    recorded by reviewers for a given application.
    """
    evaluations = evaluation_service.list_by_application(db, application_id=application_id)
    return ResponseEnvelope(data=evaluations)


@router.post(
    "",
    response_model=ResponseEnvelope[EvaluationRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create Evaluation",
)
def create_evaluation(data: EvaluationCreate, db: Session = Depends(get_db)):
    """
    Record a reviewer's qualitative evaluation. Will fail if an evaluation by
    this reviewer already exists for the same application — use /upsert instead.
    """
    evaluation = evaluation_service.create_evaluation(db, data)
    return ResponseEnvelope(data=evaluation, message="Evaluation recorded successfully.")


@router.post(
    "/upsert",
    response_model=ResponseEnvelope[EvaluationRead],
    status_code=status.HTTP_200_OK,
    summary="Create or Update Evaluation (Upsert)",
    description=(
        "Creates a new evaluation or updates an existing Draft evaluation for the same "
        "reviewer+application pair. This is the primary endpoint for the review form — "
        "it supports both 'Save as Draft' and 'Submit Final Evaluation' without raising "
        "conflict errors on re-submission. "
        "reviewer_id is optional; defaults to the first admin user (MVP mode)."
    ),
)
def upsert_evaluation(data: EvaluationUpsert, db: Session = Depends(get_db)):
    evaluation = evaluation_service.upsert_evaluation(db, data)
    action = "submitted" if evaluation.evaluation_status == "Submitted" else "saved as draft"
    return ResponseEnvelope(
        data=evaluation,
        message=f"Evaluation {action} successfully.",
    )


@router.get(
    "/{id}",
    response_model=ResponseEnvelope[EvaluationRead],
    summary="Get Evaluation by ID",
)
def get_evaluation(id: UUID, db: Session = Depends(get_db)):
    evaluation = evaluation_service.get(db, id)
    return ResponseEnvelope(data=evaluation)


@router.patch(
    "/{id}",
    response_model=ResponseEnvelope[EvaluationRead],
    summary="Update Evaluation",
)
def update_evaluation(id: UUID, data: EvaluationUpdate, db: Session = Depends(get_db)):
    """
    Update an existing evaluation — change qualitative ratings, reviewer notes,
    strengths, concerns, or finalize/submit. Submitted evaluations may still be
    updated by the same reviewer.
    """
    evaluation = evaluation_service.update_evaluation(db, id, data)
    return ResponseEnvelope(data=evaluation, message="Evaluation updated successfully.")


@router.delete(
    "/{id}",
    response_model=ResponseEnvelope[None],
    summary="Delete Draft Evaluation",
)
def delete_evaluation(id: UUID, db: Session = Depends(get_db)):
    """
    Delete a Draft evaluation. Submitted evaluations cannot be deleted
    to preserve review auditability.
    """
    evaluation_service.delete_evaluation(db, id)
    return ResponseEnvelope(data=None, message="Draft evaluation deleted.")