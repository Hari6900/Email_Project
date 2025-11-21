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
    # Restrict domain: Only stackly.com emails allowed
    if not user_in.email.lower().endswith("@stackly.com"):
        raise HTTPException(
            status_code=400,
            detail="Only stackly.com domain email is allowed"
        )
    # 1. Check if email already exists
    if User.objects.filter(email=user_in.email).exists():
        raise HTTPException(
            status_code=400,
            detail="Email already registered",
        )

    # 2. Create the user (Hash the password!)
    # We use our 'get_password_hash' tool from security.py
    user = User(
        email=user_in.email,
        role="STAFF", # Default role for new signups
        is_active=True
    )
    user.set_password(user_in.password) # Django's built-in password setter handles hashing too, but explicit hashing is safer in API
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
    Update my own first/last name.
    """
    # Update fields if they are provided
    if user_update.first_name is not None:
        current_user.first_name = user_update.first_name
    if user_update.last_name is not None:
        current_user.last_name = user_update.last_name
    
    current_user.save()
    return current_user