from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from app.models.interview import Interview
from app.models.application import Application
from app.models.user import User
from app.schemas.interview import InterviewCreate, InterviewUpdate
from app.models.enums import InterviewStatus
from app.services.base import BaseService


class InterviewService(BaseService[Interview]):
    def __init__(self):
        super().__init__(Interview)

    def list_interviews(
        self,
        db: Session,
        application_id: Optional[UUID] = None,
        status: Optional[InterviewStatus] = None,
    ) -> List[Interview]:
        """
        List interview records, optionally filtered by application_id and status.
        Eagerly loads application, applicant, and role for rich display.
        """
        query = db.query(Interview).options(
            joinedload(Interview.application).joinedload(Application.applicant),
            joinedload(Interview.application).joinedload(Application.role),
        )
        if application_id:
            query = query.filter(Interview.application_id == application_id)
        if status:
            query = query.filter(Interview.status == status.value)
        return query.order_by(Interview.scheduled_at.desc()).all()

    def list_by_application(self, db: Session, application_id: UUID) -> List[Interview]:
        return self.list_interviews(db, application_id=application_id)

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