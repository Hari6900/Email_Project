from fastapi import APIRouter, Depends, HTTPException
from asgiref.sync import sync_to_async
from django_backend.models import UserProfile
from fastapi_app.schemas.profile_schemas import ProfileCreate, ProfileRead
from fastapi_app.routers.auth import get_current_user
from django_backend.models import User

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
