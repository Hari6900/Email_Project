from fastapi import APIRouter, Depends, HTTPException, status
from django.contrib.auth import get_user_model

from django_backend.models import Email
from fastapi_app.schemas.email_schemas import EmailCreate, EmailReply, EmailUpdate
from fastapi_app.dependencies.auth import get_current_user  

router = APIRouter()
User = get_user_model()


# Helper: Only stackly.com emails allowed
def ensure_stackly_email(email: str):
    if not email.endswith("@stackly.com"):
        raise HTTPException(
            status_code=400,
            detail="Only stackly.com email addresses are allowed"
        )


# SEND A EMAIL
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


# REPLY TO A EMAIL
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


# INBOX
@router.get("/inbox")
def inbox(current_user: User = Depends(get_current_user)):
    msgs = Email.objects.filter(
        receiver=current_user, 
        is_deleted_by_receiver=False 
    ).order_by("-created_at")

    return [
        {
            "id": m.id,
            "from": m.sender.email,
            "subject": m.subject,
            "body": m.body,
            "date": m.created_at,
            "is_important": m.is_important,
            "is_favorite": m.is_favorite,
        }
        for m in msgs
    ]


# SENT EMAILS
@router.get("/sent")
def sent(current_user: User = Depends(get_current_user)):
    msgs = Email.objects.filter(
        sender=current_user, 
        is_deleted_by_sender=False
    ).order_by("-created_at")

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


# FULL THREAD VIEW
@router.get("/thread/{email_id}")
def email_thread(
    email_id: int,
    current_user: User = Depends(get_current_user)
):
    try:
        root = Email.objects.get(id=email_id)
    except Email.DoesNotExist:
        raise HTTPException(status_code=404, detail="Email not found")

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
    
   # DELETE EMAIL (Soft Delete) 
@router.delete("/{email_id}", status_code=204)
def delete_email(email_id: int, current_user: User = Depends(get_current_user)):
    try:
        email_obj = Email.objects.get(id=email_id)
    except Email.DoesNotExist:
        raise HTTPException(status_code=404, detail="Email not found")

    # Logic: Mark as deleted based on who the user is
    if current_user == email_obj.sender:
        email_obj.is_deleted_by_sender = True
    elif current_user == email_obj.receiver:
        email_obj.is_deleted_by_receiver = True
    else:
        raise HTTPException(status_code=403, detail="Not authorized to delete this email")

    email_obj.save()
    return None    

# UPDATE FLAGS (Important/Favorite)
@router.patch("/{email_id}")
def update_email_flags(
    email_id: int, 
    data: EmailUpdate, 
    current_user: User = Depends(get_current_user)
):
    try:
        email_obj = Email.objects.get(id=email_id)
    except Email.DoesNotExist:
        raise HTTPException(status_code=404, detail="Email not found")

    # Logic: Only the RECEIVER can flag emails in their inbox
    if current_user != email_obj.receiver:
        raise HTTPException(status_code=403, detail="You can only flag emails in your inbox")

    # Update fields if provided
    if data.is_important is not None:
        email_obj.is_important = data.is_important
    if data.is_favorite is not None:
        email_obj.is_favorite = data.is_favorite
    
    email_obj.save()
    return {"message": "Email updated", "is_important": email_obj.is_important, "is_favorite": email_obj.is_favorite}
