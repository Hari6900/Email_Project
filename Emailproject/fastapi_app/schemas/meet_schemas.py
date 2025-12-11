from pydantic import BaseModel, computed_field
from datetime import datetime

class MeetingCreate(BaseModel):
    title: str = "New Meeting" 

class MeetingRead(BaseModel):
    id: int
    title: str
    meeting_code: str
    created_at: datetime
    is_active: bool
    
    @computed_field
    def join_url(self) -> str:
        return f"https://meet.jit.si/Stackly-Meeting-{self.meeting_code}" 

    class Config:
        from_attributes = True