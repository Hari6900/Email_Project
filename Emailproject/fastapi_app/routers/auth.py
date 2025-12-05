from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import timedelta
from asgiref.sync import sync_to_async

from ..core.security import (
    verify_password, create_access_token,
    create_password_reset_token, decode_access_token
)
from ..core.config import settings
from ..schemas.user_schemas import Token, ForgotPasswordRequest, ResetPasswordRequest

from django.contrib.auth import get_user_model
User = get_user_model()

router = APIRouter()

# OAuth2 token extractor for protected routes
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# ============================================================
# NEW: get_current_user (required for Task creation)
# ============================================================
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Extracts the logged-in user from the JWT access token.
    Used in authenticated endpoints like:
    - create task
    - create chat room
    - send messages
    """

    # Decode token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # Get user from Django ORM
    user = await sync_to_async(User.objects.filter(email=email).first)()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user


# ============================================================
# LOGIN
# ============================================================
@router.post("/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    User = get_user_model()
    email = form_data.username

    # 1. Email domain validation (only stackly.com allowed)
    if not email.endswith("@stackly.com"):
        raise HTTPException(
            status_code=400,
            detail="Only stackly.com email accounts are allowed"
        )

    # 2. Check User
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Check Password
    if not user.check_password(form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Generate Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


# ============================================================
# FORGOT PASSWORD
# ============================================================
@router.post("/forgot-password", status_code=200)
def forgot_password(data: ForgotPasswordRequest):
    user = User.objects.filter(email=data.email).first()

    if not user:
        return {"message": "If this email exists, a reset link has been sent."}

    reset_token = create_password_reset_token(user.email)

    print("\n==========================================")
    print(f" PASSWORD RESET EMAIL FOR: {user.email}")
    print(f" LINK: {reset_token}")
    print("==========================================\n")

    return {"message": "If this email exists, a reset link has been sent."}


# ============================================================
# RESET PASSWORD
# ============================================================
@router.post("/reset-password", status_code=200)
def reset_password(data: ResetPasswordRequest):
    payload = decode_access_token(data.token)
    
    if not payload:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    if payload.get("type") != "reset":
        raise HTTPException(status_code=400, detail="Invalid token type")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=400, detail="Invalid token payload")

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")

    user.set_password(data.new_password)
    user.save()

    return {"message": "Password reset successfully. You can now login with your new password."}
