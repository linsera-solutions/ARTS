from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.applicant import Applicant, Experience, PortfolioItem, ApplicantSkill
from app.schemas.applicant import ApplicantCreate, ApplicantUpdate
from app.services.base import BaseService


class ApplicantService(BaseService[Applicant]):
    def __init__(self):
        super().__init__(Applicant)

    def list_applicants(self, db: Session, skip: int = 0, limit: int = 100) -> List[Applicant]:
        return db.query(Applicant).offset(skip).limit(limit).all()

    def create_applicant(self, db: Session, data: ApplicantCreate) -> Applicant:
        applicant = Applicant(
            full_name=data.full_name,
            email=str(data.email),
            phone_number=data.phone_number,
            location=data.location,
            external_profile_link=data.external_profile_link,
            applicant_status=data.applicant_status.value,
        )
        db.add(applicant)
        db.flush()

        # Add child experiences if provided
        if data.experiences:
            for exp_in in data.experiences:
                exp = Experience(
                    applicant_id=applicant.id,
                    title=exp_in.title,
                    organization=exp_in.organization,
                    start_date=exp_in.start_date,
                    end_date=exp_in.end_date,
                    description=exp_in.description,
                )
                db.add(exp)

        # Add portfolio items if provided
        if data.portfolio_items:
            for port_in in data.portfolio_items:
                port = PortfolioItem(
                    applicant_id=applicant.id,
                    title=port_in.title,
                    description=port_in.description,
                    reference_link=port_in.reference_link,
                    attachment_reference=port_in.attachment_reference,
                )
                db.add(port)

        # Add skills if provided
        if data.skills:
            for sk_in in data.skills:
                sk = ApplicantSkill(
                    applicant_id=applicant.id,
                    skill_id=sk_in.skill_id,
                    proficiency_level=sk_in.proficiency_level.value if sk_in.proficiency_level else None,
                    years_of_experience=sk_in.years_of_experience,
                )
                db.add(sk)

        db.commit()
        db.refresh(applicant)
        return applicant

    def update_applicant(self, db: Session, id: UUID, data: ApplicantUpdate) -> Applicant:
        applicant = self.get(db, id)
        update_data = data.model_dump(exclude_unset=True)

        for key, value in update_data.items():
            if key == "applicant_status" and value is not None:
                setattr(applicant, key, value.value)
            elif key == "email" and value is not None:
                setattr(applicant, key, str(value))
            else:
                setattr(applicant, key, value)

        db.commit()
        db.refresh(applicant)
        return applicant


applicant_service = ApplicantService()
