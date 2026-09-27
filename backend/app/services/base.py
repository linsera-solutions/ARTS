from typing import Generic, TypeVar, Type, Optional, List, Any
from uuid import UUID
from sqlalchemy.orm import Session
from app.db.session import Base
from app.core.exceptions import NotFoundException

ModelType = TypeVar("ModelType", bound=Base)


class BaseService(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: UUID) -> ModelType:
        item = db.query(self.model).filter(self.model.id == id).first()
        if not item:
            raise NotFoundException(f"{self.model.__name__} with ID {id} not found.")
        return item

    def get_optional(self, db: Session, id: UUID) -> Optional[ModelType]:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_all(self, db: Session, skip: int = 0, limit: int = 100) -> List[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def count(self, db: Session) -> int:
        return db.query(self.model).count()

    def delete(self, db: Session, id: UUID) -> None:
        item = self.get(db, id)
        db.delete(item)
        db.commit()
