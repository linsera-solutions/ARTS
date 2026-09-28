from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.application import (
    ApplicationRead,
    ApplicationDetailRead,
    ApplicationCreate,
    ApplicationStatusUpdate,
    ApplicationIntakeRequest,
    ApplicationBatchIntakeRequest,
    IntakeSummaryResponse,
    IntakeResultItem,
    AllowedTransitionsResponse,
)
from app.schemas.common import ResponseEnvelope, PaginatedResponse
from app.models.enums import ApplicationStatus
from app.services.application_service import application_service

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[PaginatedResponse[ApplicationRead]], summary="Search & Filter Applications")
def list_applications(
    query: Optional[str] = Query(None, description="Search query across candidate name, email, role, motivation"),
    role_id: Optional[UUID] = Query(None, description="Filter by Target Role ID"),
    status_filter: Optional[ApplicationStatus] = Query(None, alias="status", description="Filter by Application Status"),
    location: Optional[str] = Query(None, description="Filter by candidate location"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """
    Search and filter applications across roles, statuses, and candidate keywords.
    """
    skip = (page - 1) * page_size
    items, total = application_service.search_applications(
        db,
        query=query,
        role_id=role_id,
        status=status_filter,
        location=location,
        skip=skip,
        limit=page_size,
    )
    paginated = PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)
    return ResponseEnvelope(data=paginated)


@router.post("", response_model=ResponseEnvelope[ApplicationRead], status_code=status.HTTP_201_CREATED, summary="Create Application")
def create_application(
    data: ApplicationCreate,
    db: Session = Depends(get_db),
):
    """
    Record an application manually for an existing candidate and role.
    """
    app = application_service.create_application(db, data)
    return ResponseEnvelope(data=app, message="Application registered successfully.")


@router.post("/intake", response_model=ResponseEnvelope[IntakeResultItem], status_code=status.HTTP_201_CREATED, summary="Ingest Single Google Forms Submission")
def process_intake(
    data: ApplicationIntakeRequest,
    db: Session = Depends(get_db),
):
    """
    FR-001, FR-005, FR-007: Ingest single Google Forms response.
    Idempotently matches existing candidate by email without duplicates.
    """
    result = application_service.process_intake(db, data)
    return ResponseEnvelope(data=result, message=result.reason)


@router.post("/intake/batch", response_model=ResponseEnvelope[IntakeSummaryResponse], status_code=status.HTTP_200_OK, summary="Batch Import Google Forms Submissions")
def process_batch_intake(
    data: ApplicationBatchIntakeRequest,
    db: Session = Depends(get_db),
):
    """
    FR-002, FR-003, FR-004: Ingest multiple candidate applications from external export/file.
    Validates required fields and reports accepted vs rejected counts.
    """
    summary = application_service.process_batch_intake(db, data)
    return ResponseEnvelope(
        data=summary,
        message=f"Batch intake completed: {summary.accepted} created, {summary.updated} updated, {summary.rejected} rejected.",
    )


@router.get("/{id}", response_model=ResponseEnvelope[ApplicationDetailRead], summary="Get Consolidated Application Detail")
def get_application(
    id: UUID,
    db: Session = Depends(get_db),
):
    """
    FR-011: Retrieve consolidated profile combining applicant details, portfolio links,
    experiences, claimed skills, evaluations, interviews, notes, and status audit history.
    """
    app_details = application_service.get_detailed_application(db, id)
    return ResponseEnvelope(data=app_details)


@router.get("/{id}/allowed-transitions", response_model=ResponseEnvelope[AllowedTransitionsResponse], summary="Get Permitted Status Transitions")
def get_allowed_transitions(
    id: UUID,
    db: Session = Depends(get_db),
):
    """
    Returns the current status and list of allowed next statuses for an application
    according to the approved recruitment workflow (BR-001, BR-002).
    """
    transitions = application_service.get_allowed_transitions(db, id)
    return ResponseEnvelope(data=transitions)


@router.patch("/{id}/status", response_model=ResponseEnvelope[ApplicationRead], summary="Transition Application Status")
def update_application_status(
    id: UUID,
    data: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
):
    """
    BR-001, BR-002: Perform human-authorized lifecycle status change with immutable audit logging.
    """
    app = application_service.update_status(db, id, data)
    return ResponseEnvelope(data=app, message=f"Application status changed to '{data.new_status.value}'.")
