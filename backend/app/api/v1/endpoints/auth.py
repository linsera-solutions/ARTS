from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.models.enums import AccountStatus
from app.schemas.auth import LoginRequest, TokenResponse, UserSummary
from app.schemas.common import ResponseEnvelope
from app.core.security import verify_password, create_access_token
from app.core.exceptions import UnauthorizedException, ForbiddenException
from app.core.deps import get_current_user
from app.core.config import settings

router = APIRouter()


@router.post(
    "/login",
    response_model=ResponseEnvelope[TokenResponse],
    summary="Recruiter Sign-In",
    description="Authenticates Team Lead / Recruiter credentials and issues a JWT access token.",
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    email_clean = str(data.email).lower().strip()
    user = db.query(User).filter(User.email == email_clean).first()

    if not user:
        raise UnauthorizedException("Invalid email or password.")

    if not user.hashed_password or not verify_password(data.password, user.hashed_password):
        raise UnauthorizedException("Invalid email or password.")

    if user.account_status != AccountStatus.ACTIVE.value:
        raise ForbiddenException("Account is disabled or suspended.")

    # Create JWT token
    token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.user_role,
        }
    )

    user_summary = UserSummary(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        user_role=user.user_role,
        account_status=user.account_status,
    )

    token_resp = TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        user=user_summary,
    )

    return ResponseEnvelope(data=token_resp, message="Authentication successful.")


@router.get(
    "/me",
    response_model=ResponseEnvelope[UserSummary],
    summary="Get Current User Profile",
    description="Retrieves identity and permissions for the currently authenticated recruiter session.",
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    user_summary = UserSummary(
        id=current_user.id,
        full_name=current_user.full_name,
        email=current_user.email,
        user_role=current_user.user_role,
        account_status=current_user.account_status,
    )
    return ResponseEnvelope(data=user_summary)


@router.post(
    "/logout",
    response_model=ResponseEnvelope[None],
    summary="Recruiter Sign-Out",
    description="Terminates the current recruiter session.",
)
def logout(
    current_user: User = Depends(get_current_user),
):
    return ResponseEnvelope(data=None, message="Successfully signed out.")