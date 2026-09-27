from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.interview import InterviewRead, InterviewCreate, InterviewUpdate
from app.schemas.common import ResponseEnvelope
from app.services.interview_service import interview_service

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[List[InterviewRead]], summary="List Interviews by Application")
def list_interviews(
    application_id: UUID = Query(..., description="Application ID to fetch interviews/discussions for"),
    db: Session = Depends(get_db),
):
    """
    Retrieve discussion/interview records for an application.
    """
    interviews = interview_service.list_by_application(db, application_id=application_id)
    return ResponseEnvelope(data=interviews)


@router.post("", response_model=ResponseEnvelope[InterviewRead], status_code=status.HTTP_201_CREATED, summary="Schedule Interview")
def create_interview(
    data: InterviewCreate,
    db: Session = Depends(get_db),
):
    """
    Schedule a candidate discussion or interview.
    """
    interview = interview_service.create_interview(db, data)
    return ResponseEnvelope(data=interview, message="Interview scheduled successfully.")


@router.get("/{id}", response_model=ResponseEnvelope[InterviewRead], summary="Get Interview Details")
def get_interview(
    id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get detailed interview discussion and outcome information.
    """
    interview = interview_service.get(db, id)
    return ResponseEnvelope(data=interview)


@router.patch("/{id}", response_model=ResponseEnvelope[InterviewRead], summary="Update Interview Outcome")
def update_interview(
    id: UUID,
    data: InterviewUpdate,
    db: Session = Depends(get_db),
):
    """
    Update interview details, record outcomes, or update status.
    """
    interview = interview_service.update_interview(db, id, data)
    return ResponseEnvelope(data=interview, message="Interview updated successfully.")
