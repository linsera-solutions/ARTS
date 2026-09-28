from typing import Optional
from uuid import UUID
from pydantic import EmailStr, Field
from app.schemas.common import BaseSchema
from app.models.enums import UserRole, AccountStatus


class LoginRequest(BaseSchema):
    """
    Recruiter authentication payload for signing into ARTS.
    """
    email: EmailStr = Field(..., description="Recruiter email address")
    password: str = Field(..., min_length=6, description="Recruiter password")


class UserSummary(BaseSchema):
    """
    Authenticated recruiter identity details.
    """
    id: UUID
    full_name: str
    email: EmailStr
    user_role: UserRole
    account_status: AccountStatus


class TokenResponse(BaseSchema):
    """
    JWT Access Token response returned upon successful authentication.
    """
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int
    user: UserSummary