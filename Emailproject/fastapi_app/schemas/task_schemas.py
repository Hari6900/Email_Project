from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserTiny(BaseModel):
    id: int
    email: str
    first_name: str | None = None  
    
    class Config:
        from_attributes = True

class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    priority: str = "medium"
    due_date: datetime | None = None
    assigned_to_email: str | None = None 

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assigned_to_email: str | None = None

class TaskRead(BaseModel):
    id: int
    title: str
    description: str | None
    status: str
    priority: str
    due_date: datetime | None
    created_at: datetime
    
    created_by: UserTiny
    assigned_to: UserTiny | None = None

    class Config:
        from_attributes = True
