from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.interview import Interview
from app.models.user import User
from app.schemas.interview import InterviewCreate, InterviewUpdate
from app.services.base import BaseService


class InterviewService(BaseService[Interview]):
    def __init__(self):
        super().__init__(Interview)

    def list_by_application(self, db: Session, application_id: UUID) -> List[Interview]:
        return db.query(Interview).filter(Interview.application_id == application_id).all()

    def create_interview(self, db: Session, data: InterviewCreate) -> Interview:
        interview = Interview(
            application_id=data.application_id,
            scheduled_at=data.scheduled_at,
            format=data.format,
            status=data.status.value,
            outcome_summary=data.outcome_summary,
        )
        if data.participant_user_ids:
            users = db.query(User).filter(User.id.in_(data.participant_user_ids)).all()
            interview.participants = users

        db.add(interview)
        db.commit()
        db.refresh(interview)
        return interview

    def update_interview(self, db: Session, id: UUID, data: InterviewUpdate) -> Interview:
        interview = self.get(db, id)
        update_data = data.model_dump(exclude_unset=True)

        if "participant_user_ids" in update_data:
            user_ids = update_data.pop("participant_user_ids")
            if user_ids is not None:
                users = db.query(User).filter(User.id.in_(user_ids)).all()
                interview.participants = users

        for key, value in update_data.items():
            if key == "status" and value is not None:
                setattr(interview, key, value.value)
            else:
                setattr(interview, key, value)

        db.commit()
        db.refresh(interview)
        return interview


interview_service = InterviewService()
