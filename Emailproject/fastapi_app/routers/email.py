from fastapi import APIRouter, Depends, HTTPException, status
from django.contrib.auth import get_user_model

from django_backend.models import Email
from fastapi_app.schemas.email_schemas import EmailCreate, EmailReply
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
# SEND A EMAIL
# ----------------------
@router.post("/send")
def send_email(
    data: EmailCreate,
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

    # Create email
    email_obj = Email.objects.create(
        sender=current_user,
        receiver=receiver,
        subject=data.subject,
        body=data.body
    )

    return {"message": "Email sent successfully", "id": email_obj.id}


# ----------------------
# REPLY TO A EMAIL
# ----------------------
@router.post("/reply")
def reply_email(
    data: EmailReply,
    current_user: User = Depends(get_current_user)
):
    ensure_stackly_email(current_user.email)

    try:
        parent = Email.objects.get(id=data.email_id)
    except Email.DoesNotExist:
        raise HTTPException(status_code=404, detail="Email not found")

    # Reply goes back to original sender
    reply = Email.objects.create(
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
    msgs = Email.objects.filter(receiver=current_user).order_by("-created_at")

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
# SENT EMAILS
# ----------------------
@router.get("/sent")
def sent(current_user: User = Depends(get_current_user)):
    msgs = Email.objects.filter(sender=current_user).order_by("-created_at")

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
@router.get("/thread/{email_id}")
def email_thread(
    email_id: int,
    current_user: User = Depends(get_current_user)
):
    try:
        root = Email.objects.get(id=email_id)
    except Email.DoesNotExist:
        raise HTTPException(status_code=404, detail="Email not found")

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
