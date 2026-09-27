from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.applicant import (
    ApplicantRead,
    ApplicantCreate,
    ApplicantUpdate,
    EvidenceLinkCreate,
    PortfolioItemRead,
)
from app.schemas.common import ResponseEnvelope, PaginatedResponse
from app.models.enums import ApplicantStatus
from app.services.applicant_service import applicant_service

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[PaginatedResponse[ApplicantRead]], summary="Search & List Applicants")
def list_applicants(
    query: Optional[str] = Query(None, description="Search query across candidate name, email, location, skills, experience"),
    location: Optional[str] = Query(None, description="Filter by candidate location"),
    status_filter: Optional[ApplicantStatus] = Query(None, alias="status", description="Filter by applicant status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Search and filter candidate profiles with pagination.
    """
    skip = (page - 1) * page_size
    items, total = applicant_service.search_applicants(
        db, query=query, location=location, status=status_filter, skip=skip, limit=page_size
    )
    paginated = PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)
    return ResponseEnvelope(data=paginated)


@router.post("", response_model=ResponseEnvelope[ApplicantRead], status_code=status.HTTP_201_CREATED, summary="Create Applicant")
def create_applicant(
    data: ApplicantCreate,
    db: Session = Depends(get_db),
):
    """
    FR-001: Manually create a new applicant profile with experience and evidence.
    """
    applicant = applicant_service.create_applicant(db, data)
    return ResponseEnvelope(data=applicant, message="Candidate profile created successfully.")


@router.get("/{id}", response_model=ResponseEnvelope[ApplicantRead], summary="Get Candidate Profile")
def get_applicant(
    id: UUID,
    db: Session = Depends(get_db),
):
    """
    Retrieve full candidate profile, experiences, portfolio items, and claimed skills.
    """
    applicant = applicant_service.get(db, id)
    return ResponseEnvelope(data=applicant)


@router.patch("/{id}", response_model=ResponseEnvelope[ApplicantRead], summary="Update Candidate Profile")
def update_applicant(
    id: UUID,
    data: ApplicantUpdate,
    db: Session = Depends(get_db),
):
    """
    FR-012: Edit permitted fields of an applicant profile.
    """
    applicant = applicant_service.update_applicant(db, id, data)
    return ResponseEnvelope(data=applicant, message="Candidate profile updated successfully.")


@router.post("/{id}/evidence", response_model=ResponseEnvelope[PortfolioItemRead], status_code=status.HTTP_201_CREATED, summary="Add Evidence Link")
def add_evidence_link(
    id: UUID,
    data: EvidenceLinkCreate,
    db: Session = Depends(get_db),
):
    """
    FR-015, FR-016, FR-018: Attach an evidence link or portfolio URL to an applicant profile.
    """
    evidence = applicant_service.add_evidence_link(db, id, data)
    return ResponseEnvelope(data=evidence, message="Evidence link attached successfully.")


@router.delete("/{id}/evidence/{evidence_id}", response_model=ResponseEnvelope[None], summary="Remove Evidence Link")
def remove_evidence_link(
    id: UUID,
    evidence_id: UUID,
    db: Session = Depends(get_db),
):
    """
    FR-017: Remove an evidence link from a candidate profile.
    """
    applicant_service.remove_evidence_link(db, id, evidence_id)
    return ResponseEnvelope(data=None, message="Evidence link removed successfully.")


@router.patch("/{id}/archive", response_model=ResponseEnvelope[ApplicantRead], summary="Archive Applicant")
def archive_applicant(
    id: UUID,
    db: Session = Depends(get_db),
):
    """
    FR-010: Archive an applicant record, removing them from active review while preserving history.
    """
    applicant = applicant_service.archive_applicant(db, id)
    return ResponseEnvelope(data=applicant, message="Applicant archived successfully.")
