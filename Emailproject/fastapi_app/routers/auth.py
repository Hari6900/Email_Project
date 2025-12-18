import pyotp
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from datetime import timedelta
from asgiref.sync import sync_to_async
from django_backend.models import LoginActivity
from ..core.security import (
    verify_password, create_access_token,
    create_password_reset_token, decode_access_token
)
from ..core.config import settings
from ..schemas.user_schemas import Token, ForgotPasswordRequest, ResetPasswordRequest

from django.contrib.auth import get_user_model
User = get_user_model()

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# NEW: get_current_user (required for Task creation)
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

# LOGIN
@router.post("/login", response_model=Token)
def login_for_access_token(
    request: Request, 
    form_data: OAuth2PasswordRequestForm = Depends(),
    otp: str | None = Query(default=None, description="2FA Code if enabled") 
):
    User = get_user_model()
    email = form_data.username

    # 1. Standard Authentication
    if not email.endswith("@stackly.com"):
        raise HTTPException(status_code=400, detail="Only stackly.com emails allowed")

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    if not user.check_password(form_data.password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # 2. 2FA ENFORCEMENT LOGIC (The New Guard)
    # Check if user has 2FA enabled
    is_2fa_on = False
    if hasattr(user, 'profile') and user.profile.is_2fa_enabled:
        is_2fa_on = True

    if is_2fa_on:
        if not otp:
            raise HTTPException(
                status_code=401, 
                detail="2FA Required. Please provide the 'otp' parameter."
            )
        
        secret = user.profile.two_factor_secret
        if not secret:
             raise HTTPException(status_code=401, detail="2FA Configuration Error")

        totp = pyotp.TOTP(secret)
        if not totp.verify(otp):
             raise HTTPException(status_code=401, detail="Invalid 2FA Code")

    # --- PRIVACY CHECK & LOGGING (Your existing code) ---
    should_record = True 
    try:
        if hasattr(user, 'profile'):
             should_record = user.profile.store_activity
    except Exception:
        pass

    if should_record:
        client_ip = request.client.host
        user_agent = request.headers.get("user-agent")
        LoginActivity.objects.create(user=user, ip_address=client_ip, user_agent=user_agent)
    
    # 4. Generate Token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
<<<<<<< Updated upstream
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
=======
    access_token = create_access_token (
        data={"sub": user.email},
        expires_delta=access_token_expires,
>>>>>>> Stashed changes
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
# FORGOT PASSWORD
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

# RESET PASSWORD
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

