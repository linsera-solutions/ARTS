from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.evaluation import EvaluationRead, EvaluationCreate, EvaluationUpdate
from app.schemas.common import ResponseEnvelope
from app.services.evaluation_service import evaluation_service

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[List[EvaluationRead]], summary="List Evaluations by Application")
def list_evaluations(
    application_id: UUID = Query(..., description="Application ID to fetch evaluations for"),
    db: Session = Depends(get_db),
):
    """
    Retrieve structured evaluations and criterion scores for an application.
    """
    evaluations = evaluation_service.list_by_application(db, application_id=application_id)
    return ResponseEnvelope(data=evaluations)


@router.post("", response_model=ResponseEnvelope[EvaluationRead], status_code=status.HTTP_201_CREATED, summary="Create Evaluation")
def create_evaluation(
    data: EvaluationCreate,
    db: Session = Depends(get_db),
):
    """
    Record a reviewer's evaluation and criterion-level scores.
    """
    evaluation = evaluation_service.create_evaluation(db, data)
    return ResponseEnvelope(data=evaluation, message="Evaluation recorded successfully.")


@router.get("/{id}", response_model=ResponseEnvelope[EvaluationRead], summary="Get Evaluation by ID")
def get_evaluation(
    id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get detailed evaluation with criterion scores.
    """
    evaluation = evaluation_service.get(db, id)
    return ResponseEnvelope(data=evaluation)


@router.patch("/{id}", response_model=ResponseEnvelope[EvaluationRead], summary="Update Evaluation")
def update_evaluation(
    id: UUID,
    data: EvaluationUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an evaluation or finalize/submit it.
    """
    evaluation = evaluation_service.update_evaluation(db, id, data)
    return ResponseEnvelope(data=evaluation, message="Evaluation updated successfully.")
