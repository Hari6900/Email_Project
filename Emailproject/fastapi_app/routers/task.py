from fastapi import APIRouter, Depends, HTTPException
from asgiref.sync import sync_to_async

from django_backend.models import Email, Task, User
from fastapi_app.schemas.task_schemas import TaskRead
from fastapi_app.routers.auth import get_current_user


router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/from-email/{email_id}", response_model=TaskRead)
async def create_task_from_email(
    email_id: int,
    current_user: User = Depends(get_current_user)
):
    """
    Convert an email into a Task.
    Auto-fills:
      • Task title from Email.subject
      • Task description from Email.body
    """

    # Fetch email
    email = await sync_to_async(Email.objects.filter(id=email_id).first)()

    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    # Auto-fill task fields
    title = email.subject or f"Task from Email #{email.id}"
    description = email.body or "No email content available."

    # Create the task
    task = await sync_to_async(Task.objects.create)(
        title=title,
        description=description,
        created_by=current_user,
        email=email,
    )

    return task
