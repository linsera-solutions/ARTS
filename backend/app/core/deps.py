from typing import Optional
from uuid import UUID
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.enums import AccountStatus
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False,
)


def get_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
) -> User:
    """
    Enforces authentication for protected ARTS internal endpoints.
    Extracts Bearer token, validates signature/expiration, and resolves active user.
    """
    if not token:
        raise UnauthorizedException("Authentication token required. Please sign in.")

    payload = decode_access_token(token)
    if not payload:
        raise UnauthorizedException("Invalid, expired, or forged authentication token.")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Token payload malformed (missing subject).")

    try:
        user_id = UUID(user_id_str)
    except (ValueError, TypeError):
        raise UnauthorizedException("Token subject is not a valid identifier.")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise UnauthorizedException("Authenticated user account not found.")

    if user.account_status != AccountStatus.ACTIVE.value:
        raise ForbiddenException("User account is disabled or suspended.")

    return user


def get_optional_current_user(
    db: Session = Depends(get_db),
    token: Optional[str] = Depends(oauth2_scheme),
) -> Optional[User]:
    """
    Optional authentication helper for endpoints that allow both public access
    and enhanced access for signed-in recruiters.
    """
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    user_id_str = payload.get("sub")
    if not user_id_str:
        return None

    try:
        user = db.query(User).filter(User.id == UUID(user_id_str)).first()
        if user and user.account_status == AccountStatus.ACTIVE.value:
            return user
    except Exception:
        return None

    return None