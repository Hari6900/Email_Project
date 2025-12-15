from pydantic import BaseModel
from datetime import datetime

class NotificationRead(BaseModel):
    id: int
    message: str
    notification_type: str
    is_read: bool
    created_at: datetime
    related_id: int | None = None

    class Config:
        from_attributes = True

class NotificationUpdate(BaseModel):
    is_read: bool = True