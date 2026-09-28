from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.note import Note
from app.schemas.note import NoteCreate, NoteUpdate
from app.models.enums import NoteRelatedEntityType
from app.services.base import BaseService


class NoteService(BaseService[Note]):
    def __init__(self):
        super().__init__(Note)

    def list_by_entity(
        self, db: Session, entity_type: NoteRelatedEntityType, entity_id: UUID
    ) -> List[Note]:
        return (
            db.query(Note)
            .filter(
                Note.related_entity_type == entity_type.value,
                Note.related_entity_id == entity_id,
            )
            .order_by(Note.created_at.desc())
            .all()
        )

    def create_note(self, db: Session, data: NoteCreate) -> Note:
        note = Note(
            author_id=data.author_id,
            related_entity_type=data.related_entity_type.value,
            related_entity_id=data.related_entity_id,
            note_text=data.note_text,
            visibility=data.visibility.value,
        )
        db.add(note)
        db.commit()
        db.refresh(note)
        return note

    def update_note(self, db: Session, id: UUID, data: NoteUpdate) -> Note:
        note = self.get(db, id)
        if data.note_text is not None:
            note.note_text = data.note_text
        if data.visibility is not None:
            note.visibility = data.visibility.value
        db.commit()
        db.refresh(note)
        return note


note_service = NoteService()