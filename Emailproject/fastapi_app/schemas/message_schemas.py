from pydantic import BaseModel

class MessageCreate(BaseModel):
    receiver_email: str
    subject: str
    body: str

class ReplyCreate(BaseModel):
    message_id: int
    body: str
