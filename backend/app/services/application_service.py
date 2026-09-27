from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.application import Application, ApplicationStatusHistory
from app.models.applicant import Applicant
from app.models.team import Role
from app.schemas.application import ApplicationCreate, ApplicationStatusUpdate
from app.models.enums import ApplicationStatus
from app.services.base import BaseService
from app.core.exceptions import NotFoundException, BadRequestException


class ApplicationService(BaseService[Application]):
    def __init__(self):
        super().__init__(Application)

    def list_applications(
        self,
        db: Session,
        role_id: Optional[UUID] = None,
        status: Optional[ApplicationStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Application]:
        query = db.query(Application)
        if role_id:
            query = query.filter(Application.role_id == role_id)
        if status:
            query = query.filter(Application.current_status == status.value)
        return query.offset(skip).limit(limit).all()

    def create_application(self, db: Session, data: ApplicationCreate) -> Application:
        # Verify applicant exists
        applicant = db.query(Applicant).filter(Applicant.id == data.applicant_id).first()
        if not applicant:
            raise NotFoundException(f"Applicant with ID {data.applicant_id} does not exist.")

        # Verify role exists
        role = db.query(Role).filter(Role.id == data.role_id).first()
        if not role:
            raise NotFoundException(f"Role with ID {data.role_id} does not exist.")

        application = Application(
            applicant_id=data.applicant_id,
            role_id=data.role_id,
            motivation_statement=data.motivation_statement,
            availability_info=data.availability_info,
            current_status=ApplicationStatus.RECEIVED.value,
        )
        db.add(application)
        db.flush()

        # Record initial status in history (Audit requirement)
        history = ApplicationStatusHistory(
            application_id=application.id,
            previous_status=None,
            new_status=ApplicationStatus.RECEIVED.value,
            reason="Application created (Google Forms intake)",
        )
        db.add(history)

        db.commit()
        db.refresh(application)
        return application

    def update_status(self, db: Session, id: UUID, data: ApplicationStatusUpdate) -> Application:
        application = self.get(db, id)
        previous_status = application.current_status
        new_status = data.new_status.value

        if previous_status == new_status:
            return application

        # Update current status
        application.current_status = new_status

        # Add audit history entry
        history = ApplicationStatusHistory(
            application_id=application.id,
            previous_status=previous_status,
            new_status=new_status,
            changed_by_id=data.changed_by_id,
            reason=data.reason,
        )
        db.add(history)

        db.commit()
        db.refresh(application)
        return application


application_service = ApplicationService()
