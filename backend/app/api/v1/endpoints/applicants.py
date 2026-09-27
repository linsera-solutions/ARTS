from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.applicant import ApplicantRead, ApplicantCreate, ApplicantUpdate
from app.schemas.common import ResponseEnvelope
from app.services.applicant_service import applicant_service

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[List[ApplicantRead]], summary="List Applicants")
def list_applicants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Retrieve candidate profiles and submitted evidence.
    """
    applicants = applicant_service.list_applicants(db, skip=skip, limit=limit)
    return ResponseEnvelope(data=applicants)


@router.post("", response_model=ResponseEnvelope[ApplicantRead], status_code=status.HTTP_201_CREATED, summary="Create Applicant")
def create_applicant(
    data: ApplicantCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new candidate profile with evidence and skills.
    """
    applicant = applicant_service.create_applicant(db, data)
    return ResponseEnvelope(data=applicant, message="Applicant profile created successfully.")


@router.get("/{id}", response_model=ResponseEnvelope[ApplicantRead], summary="Get Applicant by ID")
def get_applicant(
    id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get detailed candidate profile, experiences, skills, and portfolio items.
    """
    applicant = applicant_service.get(db, id)
    return ResponseEnvelope(data=applicant)


@router.patch("/{id}", response_model=ResponseEnvelope[ApplicantRead], summary="Update Applicant")
def update_applicant(
    id: UUID,
    data: ApplicantUpdate,
    db: Session = Depends(get_db),
):
    """
    Update basic candidate profile information.
    """
    applicant = applicant_service.update_applicant(db, id, data)
    return ResponseEnvelope(data=applicant, message="Applicant updated successfully.")
