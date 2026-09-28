import uuid
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.db.session import Base
from app.models.enums import UserRole, AccountStatus


class User(Base):
    """
    E-01: User
    Internal system actor with authenticated access to administer ARTS,
    review Applications, and record Evaluations.
    """
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    user_role = Column(String(50), nullable=False, default=UserRole.REVIEWER.value)
    account_status = Column(String(50), nullable=False, default=AccountStatus.ACTIVE.value)
    hashed_password = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
