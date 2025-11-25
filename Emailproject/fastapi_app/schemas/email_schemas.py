from pydantic import BaseModel

class EmailCreate(BaseModel):
    receiver_email: str
    subject: str
    body: str

class EmailReply(BaseModel):
    email_id: int
    body: str
