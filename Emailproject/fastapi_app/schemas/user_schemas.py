import re
import requests
import hashlib
from pydantic import BaseModel, EmailStr, field_validator, ValidationInfo

class UserLogin(BaseModel):
    username: str 
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
    @field_validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 12:
            raise ValueError('Password must be at least 12 characters long')

        if not re.search(r"[A-Z]", v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r"[a-z]", v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r"\d", v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError('Password must contain at least one special character')

        try:
            sha1_password = hashlib.sha1(v.encode('utf-8')).hexdigest().upper()
            prefix, suffix = sha1_password[:5], sha1_password[5:]
            
            response = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}", timeout=5)
            
            if suffix in response.text:
                raise ValueError('This password has been exposed in a data breach. Please choose a different one.')
        except requests.RequestException:
            pass

        return v

# 2. Schema for Reading a User (Output - NO Password!)
class UserRead(BaseModel):
    id: int
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True
        
class UserUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None        