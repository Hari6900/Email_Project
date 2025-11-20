from pydantic import BaseModel, EmailStr

class UserLogin(BaseModel):
    username: str 
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    
class UserCreate(BaseModel):
    email: EmailStr
    password: str

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