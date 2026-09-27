from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.application import ApplicationRead, ApplicationCreate, ApplicationStatusUpdate
from app.schemas.common import ResponseEnvelope
from app.models.enums import ApplicationStatus
from app.services.application_service import application_service

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[List[ApplicationRead]], summary="List Applications")
def list_applications(
    role_id: Optional[UUID] = Query(None, description="Filter by Target Role ID"),
    status_filter: Optional[ApplicationStatus] = Query(None, alias="status", description="Filter by Application Status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Retrieve applications with optional filtering by role and status.
    """
    apps = application_service.list_applications(
        db, role_id=role_id, status=status_filter, skip=skip, limit=limit
    )
    return ResponseEnvelope(data=apps)


@router.post("", response_model=ResponseEnvelope[ApplicationRead], status_code=status.HTTP_201_CREATED, summary="Submit Application")
def create_application(
    data: ApplicationCreate,
    db: Session = Depends(get_db),
):
    """
    Record an application submission for a specific candidate and role.
    """
    app = application_service.create_application(db, data)
    return ResponseEnvelope(data=app, message="Application registered successfully.")


@router.get("/{id}", response_model=ResponseEnvelope[ApplicationRead], summary="Get Application Details")
def get_application(
    id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get full application details including status history, candidate details, and role info.
    """
    app = application_service.get(db, id)
    return ResponseEnvelope(data=app)


@router.patch("/{id}/status", response_model=ResponseEnvelope[ApplicationRead], summary="Update Application Status")
def update_application_status(
    id: UUID,
    data: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
):
    """
    Perform human-authorized lifecycle status transition with audit history recording.
    """
    app = application_service.update_status(db, id, data)
    return ResponseEnvelope(data=app, message=f"Application status transitioned to '{data.new_status.value}'.")
