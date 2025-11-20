from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from ..core.security import SECRET_KEY, ALGORITHM
from django.contrib.auth import get_user_model

# This tells FastAPI that the token comes from the "/login" URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    The Bouncer:
    1. Takes the token.
    2. Decodes it.
    3. Finds the user in the DB.
    4. Returns the User object (or raises 401 error).
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the JWT
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Get User from Django DB
    User = get_user_model()
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        raise credentials_exception

    return user

# --- RBAC CHECKS (Task 4) ---

def get_current_active_user(current_user = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def is_admin(current_user = Depends(get_current_active_user)):
    """Only allows users with role='ADMIN'"""
    if current_user.role != "ADMIN":
         raise HTTPException(
            status_code=403, # Forbidden
            detail="You do not have permission to access this resource"
        )
    return current_user