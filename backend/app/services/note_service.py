from typing import List
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.note import Note
from app.schemas.note import NoteCreate
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


note_service = NoteService()
