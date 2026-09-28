from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.note import NoteRead, NoteCreate, NoteUpdate
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
    Notes are reviewer-authored observations separate from the formal Evaluation record.
    """
    notes = note_service.list_by_entity(db, entity_type=entity_type, entity_id=entity_id)
    return ResponseEnvelope(data=notes)


@router.post("", response_model=ResponseEnvelope[NoteRead], status_code=status.HTTP_201_CREATED, summary="Add Note")
def create_note(data: NoteCreate, db: Session = Depends(get_db)):
    """
    Attach an informal reviewer note to an applicant or application.
    Notes are internal by default and are reviewer-authored — not applicant-facing.
    """
    note = note_service.create_note(db, data)
    return ResponseEnvelope(data=note, message="Note added successfully.")


@router.patch("/{id}", response_model=ResponseEnvelope[NoteRead], summary="Update Note")
def update_note(id: UUID, data: NoteUpdate, db: Session = Depends(get_db)):
    """
    Edit the text or visibility of an existing reviewer note.
    """
    note = note_service.update_note(db, id, data)
    return ResponseEnvelope(data=note, message="Note updated successfully.")


@router.delete("/{id}", response_model=ResponseEnvelope[None], summary="Delete Note")
def delete_note(id: UUID, db: Session = Depends(get_db)):
    """
    Remove a reviewer note permanently.
    """
    note_service.delete(db, id)
    return ResponseEnvelope(data=None, message="Note deleted successfully.")