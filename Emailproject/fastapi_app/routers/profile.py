from fastapi import APIRouter, Depends, HTTPException
from asgiref.sync import sync_to_async
from django_backend.models import UserProfile, TwoFactorAuth
from fastapi_app.schemas.profile_schemas import ProfileCreate, ProfileRead, TwoFactorVerify
from fastapi_app.routers.auth import get_current_user
from django_backend.models import User
import pyotp

router = APIRouter(prefix="/profile", tags=["Profile"])


#  CREATE PROFILE
@router.post("/", response_model=ProfileRead)
async def create_profile(
    data: ProfileCreate,
    current_user: User = Depends(get_current_user),
):
    existing = await sync_to_async(UserProfile.objects.filter(user=current_user).first)()

    if existing:
        raise HTTPException(status_code=400, detail="Profile already exists")

    profile = await sync_to_async(UserProfile.objects.create)(
        user=current_user,
        **data.dict()
    )

    return profile


# GET MY PROFILE
@router.get("/", response_model=ProfileRead)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    profile = await sync_to_async(UserProfile.objects.filter(user=current_user).first)()

    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    return profile


#  -------------------- TWO FACTOR AUTH (2FA) -------------------- 

#  SETUP 2FA (Generate Secret)
@router.post("/2fa/setup")
async def setup_2fa(current_user: User = Depends(get_current_user)):
    existing = await sync_to_async(TwoFactorAuth.objects.filter(user=current_user).first)()

    if existing:
        raise HTTPException(status_code=400, detail="2FA already setup")

    secret = pyotp.random_base32()

    await sync_to_async(TwoFactorAuth.objects.create)(
        user=current_user,
        secret=secret,
        is_enabled=False,
    )

    return {
        "message": "2FA secret generated",
        "secret": secret
    }


#  VERIFY & ENABLE 2FA
@router.post("/2fa/verify")
async def verify_2fa(
    data: TwoFactorVerify,
    current_user: User = Depends(get_current_user),
):
    record = await sync_to_async(
        TwoFactorAuth.objects.filter(user=current_user).first
    )

    if not record:
        raise HTTPException(status_code=404, detail="2FA is not setup")

    #  DIRECT SECRET MATCH (SIMPLE ACTIVATION)
    if data.code != record.secret:
        raise HTTPException(status_code=400, detail="Invalid Secret Code")

    record.is_enabled = True
    await sync_to_async(record.save)()

    return {"message": " Two-Factor Authentication Activated Successfully"}