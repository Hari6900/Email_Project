from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class MessageRead(BaseModel):
    id: int
    sender_email: str
    content: str | None
    attachment_url: str | None = None
    timestamp: datetime
    read_count: int = 0 
    is_starred: bool = False

    class Config:
        from_attributes = True

class ChatRoomRead(BaseModel):
    id: int
    name: str | None
    is_group: bool
    participants: List[str] 
    last_message: Optional[MessageRead] = None

    class Config:
        from_attributes = True

class ChatRoomCreate(BaseModel):
    participant_emails: List[str]
    name: str | None = None 
    is_group: bool = False
    
class ChatMemberUpdate(BaseModel):
    user_emails: List[str]    