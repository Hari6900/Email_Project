from fastapi import APIRouter, Depends
from django.contrib.auth import get_user_model
import secrets 
from django_backend.models import Meeting
from fastapi_app.schemas.meet_schemas import MeetingCreate, MeetingRead
from fastapi_app.dependencies.auth import get_current_user

router = APIRouter()
User = get_user_model()

# CREATE A MEETING
@router.post("/create", response_model=MeetingRead)
def create_meeting(
    data: MeetingCreate,
    current_user: User = Depends(get_current_user)
):
    code = secrets.token_urlsafe(8)

    meeting = Meeting.objects.create(
        host=current_user,
        title=data.title,
        meeting_code=code
    )

    return meeting

# LIST MY MEETINGS
@router.get("/list", response_model=list[MeetingRead])
def list_my_meetings(current_user: User = Depends(get_current_user)):
    meetings = Meeting.objects.filter(host=current_user).order_by("-created_at")

    return meetings