from pydantic import BaseModel
from datetime import date

class ProfileCreate(BaseModel):
    full_name: str
    display_name: str
    phone_number: str | None = None
    date_of_birth: date | None = None
    address: str | None = None
    language: str = "English"

    #  LIVE CURRENT DATE 
    date_format: date = date.today()

class ProfileRead(ProfileCreate):
    id: int

    class Config:
        from_attributes = True
