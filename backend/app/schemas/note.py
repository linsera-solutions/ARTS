from typing import Optional
from datetime import datetime
from uuid import UUID
from pydantic import Field
from app.schemas.common import BaseSchema
from app.models.enums import NoteRelatedEntityType, NoteVisibility


class NoteBase(BaseSchema):
    related_entity_type: NoteRelatedEntityType
    related_entity_id: UUID
    note_text: str = Field(..., min_length=1, description="Content of the note")
    visibility: NoteVisibility = Field(default=NoteVisibility.INTERNAL)


class NoteCreate(NoteBase):
    author_id: UUID


class NoteUpdate(BaseSchema):
    note_text: Optional[str] = Field(None, min_length=1)
    visibility: Optional[NoteVisibility] = None


class NoteRead(NoteBase):
    id: UUID
    author_id: UUID
    created_at: datetime
    updated_at: datetime