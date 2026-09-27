from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.team import Role
from app.models.applicant import Skill
from app.schemas.role import RoleCreate, RoleUpdate
from app.services.base import BaseService
from app.core.exceptions import NotFoundException, ConflictException


class RoleService(BaseService[Role]):
    def __init__(self):
        super().__init__(Role)

    def list_roles(self, db: Session, skip: int = 0, limit: int = 100) -> List[Role]:
        return db.query(Role).offset(skip).limit(limit).all()

    def create_role(self, db: Session, data: RoleCreate) -> Role:
        existing = db.query(Role).filter(Role.role_name == data.role_name).first()
        if existing:
            raise ConflictException(f"Role with name '{data.role_name}' already exists.")

        role = Role(
            role_name=data.role_name,
            role_description=data.role_description,
            number_of_openings=data.number_of_openings,
            role_status=data.role_status.value,
            application_deadline=data.application_deadline,
            team_id=data.team_id,
        )

        if data.desired_skill_ids:
            skills = db.query(Skill).filter(Skill.id.in_(data.desired_skill_ids)).all()
            role.desired_skills = skills

        db.add(role)
        db.commit()
        db.refresh(role)
        return role

    def update_role(self, db: Session, id: UUID, data: RoleUpdate) -> Role:
        role = self.get(db, id)
        update_data = data.model_dump(exclude_unset=True)
        
        if "role_name" in update_data and update_data["role_name"] != role.role_name:
            existing = db.query(Role).filter(Role.role_name == update_data["role_name"]).first()
            if existing:
                raise ConflictException(f"Role with name '{update_data['role_name']}' already exists.")

        for key, value in update_data.items():
            if key == "role_status" and value is not None:
                setattr(role, key, value.value)
            else:
                setattr(role, key, value)

        db.commit()
        db.refresh(role)
        return role


role_service = RoleService()
