from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.role import RoleRead, RoleCreate, RoleUpdate
from app.schemas.common import ResponseEnvelope
from app.services.role_service import role_service

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[List[RoleRead]], summary="List Roles")
def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Retrieve all recruitment target roles.
    """
    roles = role_service.list_roles(db, skip=skip, limit=limit)
    return ResponseEnvelope(data=roles)


@router.post("", response_model=ResponseEnvelope[RoleRead], status_code=status.HTTP_201_CREATED, summary="Create Role")
def create_role(
    data: RoleCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new recruitment target role.
    """
    role = role_service.create_role(db, data)
    return ResponseEnvelope(data=role, message="Role created successfully.")


@router.get("/{id}", response_model=ResponseEnvelope[RoleRead], summary="Get Role by ID")
def get_role(
    id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get detailed information for a specific role.
    """
    role = role_service.get(db, id)
    return ResponseEnvelope(data=role)


@router.patch("/{id}", response_model=ResponseEnvelope[RoleRead], summary="Update Role")
def update_role(
    id: UUID,
    data: RoleUpdate,
    db: Session = Depends(get_db),
):
    """
    Update an existing role.
    """
    role = role_service.update_role(db, id, data)
    return ResponseEnvelope(data=role, message="Role updated successfully.")
