from fastapi_app.core.status_manager import StatusManager
from typing import List
from fastapi import APIRouter, HTTPException, status, Depends, Body
from django.contrib.auth import get_user_model
from ..schemas.user_schemas import UserCreate, UserRead, UserUpdate
from ..dependencies.permissions import get_current_active_user, is_admin, get_current_user
from ..core.security import get_password_hash

User = get_user_model()
router = APIRouter()

@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate):
    """
    Create a new user.
    """
    if not user_in.email.lower().endswith("@stackly.com"):
        raise HTTPException(
            status_code=400,
            detail="Only stackly.com domain email is allowed"
        )
    
    if User.objects.filter(email=user_in.email).exists():
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    # 2. Create the user (Hash the password!)
    user = User(
    email=user_in.email,
    first_name=user_in.first_name,         
    last_name=user_in.last_name,
    dob=user_in.dob,                  
    mobile_number=user_in.mobile_number,  
    gender=user_in.gender,
    is_active=True
)
    user.set_password(user_in.password) 
    user.save()

    return user

@router.get("/me", response_model=UserRead)
def read_users_me(current_user = Depends(get_current_active_user)):
    """
    Fetch my own profile. 
    Requires a valid Login Token.
    """
    return current_user

@router.get("/", response_model=List[UserRead])
def read_all_users(
    skip: int = 0, 
    limit: int = 100, 
    current_user = Depends(is_admin) 
):
    """
    Fetch ALL users. 
    Only accessible by ADMIN users.
    """
    User = get_user_model()
    users = User.objects.all()[skip : skip + limit]
    return users

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int, 
    current_user = Depends(is_admin) 
):
    """
    Delete a user by ID. 
    Only accessible by ADMIN users.
    """
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
        user.delete()
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="User not found")
    
    return None

#  UPDATE MY PROFILE 
@router.patch("/me", response_model=UserRead)
def update_user_me(
    user_update: UserUpdate, 
    current_user = Depends(get_current_active_user)
):
    """
    Update my own profile details.
    """
    update_data = user_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(current_user, key, value)
    
    current_user.save()
    return current_user

@router.put("/status")
async def update_my_status(
    status: str = Body(..., embed=True), 
    current_user: User = Depends(get_current_user)
):
    """
    Manually update status (e.g., to 'DND', 'AVAILABLE', 'AWAY').
    """
    valid_statuses = ["AVAILABLE", "DND", "BRB", "AWAY", "OFFLINE"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")

    await StatusManager.request_status_change(current_user.id, status, is_manual=True)

    return {"message": f"Status updated to {status}"}