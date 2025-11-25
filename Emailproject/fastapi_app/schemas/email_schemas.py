from pydantic import BaseModel

class EmailCreate(BaseModel):
    receiver_email: str
    subject: str
    body: str

class EmailReply(BaseModel):
    email_id: int
    body: str
    
class EmailUpdate(BaseModel):
    is_important: bool | None = None
    is_favorite: bool | None = None    
