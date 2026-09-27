from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.note import NoteRead, NoteCreate
from app.schemas.common import ResponseEnvelope
from app.models.enums import NoteRelatedEntityType
from app.services.note_service import note_service

router = APIRouter()


@router.get("", response_model=ResponseEnvelope[List[NoteRead]], summary="List Notes by Entity")
def list_notes(
    entity_type: NoteRelatedEntityType = Query(..., description="Entity type: Applicant or Application"),
    entity_id: UUID = Query(..., description="Target Entity ID"),
    db: Session = Depends(get_db),
):
    """
    Retrieve informal reviewer annotations for an applicant or application.
    """
    notes = note_service.list_by_entity(db, entity_type=entity_type, entity_id=entity_id)
    return ResponseEnvelope(data=notes)


@router.post("", response_model=ResponseEnvelope[NoteRead], status_code=status.HTTP_201_CREATED, summary="Add Note")
def create_note(
    data: NoteCreate,
    db: Session = Depends(get_db),
):
    """
    Attach an informal note to an applicant or application.
    """
    note = note_service.create_note(db, data)
    return ResponseEnvelope(data=note, message="Note added successfully.")


@router.delete("/{id}", response_model=ResponseEnvelope[None], summary="Delete Note")
def delete_note(
    id: UUID,
    db: Session = Depends(get_db),
):
    """
    Remove a note.
    """
    note_service.delete(db, id)
    return ResponseEnvelope(data=None, message="Note deleted successfully.")
