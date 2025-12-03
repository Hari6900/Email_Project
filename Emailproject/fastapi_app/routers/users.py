from typing import List
from fastapi import APIRouter, HTTPException, status, Depends
from django.contrib.auth import get_user_model
from ..schemas.user_schemas import UserCreate, UserRead, UserUpdate
from ..dependencies.permissions import get_current_active_user, is_admin
from ..dependencies.permissions import get_current_active_user
from ..core.security import get_password_hash

router = APIRouter()

@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(user_in: UserCreate):
    """
    Create a new user.
    """
    User = get_user_model()
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
        gender=user_in.gender,           
        nationality=user_in.nationality,
        role="STAFF", 
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
    current_user = Depends(is_admin) # <--- The Bouncer! Only Admins allowed.
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
    current_user = Depends(is_admin) # <--- Bouncer: Admins only!
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

# 🟡 UPDATE MY PROFILE (Any Logged In User)
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