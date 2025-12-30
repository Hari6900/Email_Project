import re
import requests
import hashlib
from datetime import date
from typing import Optional
from pydantic import BaseModel, EmailStr, field_validator, model_validator


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    dob: Optional[date]
    mobile_number: Optional[str]
    gender: str
    password: str
    confirm_password: str

    @field_validator("password")
    def validate_password_strength(cls, v):
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one number")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")

        try:
            sha1_password = hashlib.sha1(v.encode("utf-8")).hexdigest().upper()
            prefix, suffix = sha1_password[:5], sha1_password[5:]
            response = requests.get(
                f"https://api.pwnedpasswords.com/range/{prefix}",
                timeout=5,
            )
            if suffix in response.text:
                raise ValueError(
                    "This password has been exposed in a data breach. Please choose a different one."
                )
        except requests.RequestException:
            pass

        return v

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Password and confirm password do not match")
        return self


class UserRead(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    last_name: Optional[str] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None
    role: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    gender: Optional[str] = None
    nationality: Optional[str] = None


# 🔹 Forgot password → send OTP to mobile
class ForgotPasswordRequest(BaseModel):
    mobile_number: str


# 🔹 RESET PASSWORD (kept for auth.py import compatibility)
class ResetPasswordRequest(BaseModel):
    mobile_number: str
    otp: str
    new_password: str

    @field_validator("new_password")
    def validate_password_strength(cls, v):
        return UserCreate.validate_password_strength(v)


# 🔹 Alias (optional but clean)
ResetPasswordWithOTP = ResetPasswordRequest


class ForgotUsernameRequest(BaseModel):
    phone_number: str
