from fastapi import APIRouter, Depends, HTTPException, status
from django.contrib.auth import get_user_model

from django_backend.models import Message
from fastapi_app.schemas.message_schemas import MessageCreate, ReplyCreate
from fastapi_app.dependencies.auth import get_current_user  

router = APIRouter()
User = get_user_model()


# ----------------------
# Helper: Only stackly.com emails allowed
# ----------------------
def ensure_stackly_email(email: str):
    if not email.endswith("@stackly.com"):
        raise HTTPException(
            status_code=400,
            detail="Only stackly.com email addresses are allowed"
        )


# ----------------------
# SEND A MESSAGE
# ----------------------
@router.post("/send")
def send_message(
    data: MessageCreate,
    current_user: User = Depends(get_current_user)   # <-- FIXED
):

    # Validate sender + receiver domains
    ensure_stackly_email(current_user.email)
    ensure_stackly_email(data.receiver_email)

    # Validate receiver exists
    try:
        receiver = User.objects.get(email=data.receiver_email)
    except User.DoesNotExist:
        raise HTTPException(status_code=404, detail="Receiver does not exist")

    # Create message
    msg = Message.objects.create(
        sender=current_user,
        receiver=receiver,
        subject=data.subject,
        body=data.body
    )

    return {"message": "Message sent successfully", "id": msg.id}


# ----------------------
# REPLY TO A MESSAGE
# ----------------------
@router.post("/reply")
def reply_message(
    data: ReplyCreate,
    current_user: User = Depends(get_current_user)
):
    ensure_stackly_email(current_user.email)

    try:
        parent = Message.objects.get(id=data.message_id)
    except Message.DoesNotExist:
        raise HTTPException(status_code=404, detail="Message not found")

    # Reply goes back to original sender
    reply = Message.objects.create(
        sender=current_user,
        receiver=parent.sender,
        subject=f"Re: {parent.subject}",
        body=data.body,
        parent=parent
    )

    return {"message": "Reply sent", "id": reply.id}


# ----------------------
# INBOX
# ----------------------
@router.get("/inbox")
def inbox(current_user: User = Depends(get_current_user)):
    msgs = Message.objects.filter(receiver=current_user).order_by("-created_at")

    return [
        {
            "id": m.id,
            "from": m.sender.email,
            "subject": m.subject,
            "body": m.body,
            "date": m.created_at,
        }
        for m in msgs
    ]


# ----------------------
# SENT MESSAGES
# ----------------------
@router.get("/sent")
def sent(current_user: User = Depends(get_current_user)):
    msgs = Message.objects.filter(sender=current_user).order_by("-created_at")

    return [
        {
            "id": m.id,
            "to": m.receiver.email,
            "subject": m.subject,
            "body": m.body,
            "date": m.created_at,
        }
        for m in msgs
    ]


# ----------------------
# FULL THREAD VIEW
# ----------------------
@router.get("/thread/{msg_id}")
def message_thread(
    msg_id: int,
    current_user: User = Depends(get_current_user)
):
    try:
        root = Message.objects.get(id=msg_id)
    except Message.DoesNotExist:
        raise HTTPException(status_code=404, detail="Message not found")

    # Get root + all replies
    thread = [root] + list(root.replies.all())

    return [
        {
            "id": m.id,
            "sender": m.sender.email,
            "receiver": m.receiver.email,
            "subject": m.subject,
            "body": m.body,
            "date": m.created_at,
        }
        for m in thread
    ]
