from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


#  -------------------- PROFILE --------------------

class ProfileCreate(BaseModel):
    full_name: str
    display_name: str
    phone_number: Optional[str] = None
    date_of_birth: Optional[date] = None
    bio: Optional[str] = None       #  Renamed from address → bio
    language: str = "English"
    date_format: date = date.today()   #  Current date auto-fill


class ProfileRead(ProfileCreate):
    id: int

    class Config:
        from_attributes = True


#  -------------------- ACCOUNT SETTINGS --------------------

class AccountSettingsUpdate(BaseModel):
    email_alerts: bool
    login_alerts: bool
    dark_mode: bool


class AccountSettingsRead(AccountSettingsUpdate):
    id: int

    class Config:
        from_attributes = True


#  -------------------- ACTIVITY LOGS --------------------

class ActivityLogRead(BaseModel):
    id: int
    action: str
    ip_address: str
    created_at: datetime

    class Config:
        from_attributes = True


#  -------------------- TWO-FA AUTH --------------------

class TwoFactorSetup(BaseModel):
    enable: bool


class TwoFactorVerify(BaseModel):
    code: str
