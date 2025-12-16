from fastapi import APIRouter, Depends, HTTPException, Body
from asgiref.sync import sync_to_async
from typing import List
from django_backend.models import Email, Task, User
from fastapi_app.schemas.task_schemas import TaskRead, TaskCreate, TaskUpdate
from fastapi_app.routers.auth import get_current_user
from fastapi_app.routers.notifications import create_notification

router = APIRouter(prefix="/tasks", tags=["Tasks"])

# 1. LIST MY TASKS (Dashboard)
@router.get("/", response_model=List[TaskRead])
def list_my_tasks(current_user: User = Depends(get_current_user)):
    return Task.objects.filter(assigned_to=current_user) | Task.objects.filter(created_by=current_user)

# 2. CREATE TASK (Manual)
@router.post("/", response_model=TaskRead)
def create_task(data: TaskCreate, current_user: User = Depends(get_current_user)):
    assignee = None
    if data.assigned_to_email:
        try:
            assignee = User.objects.get(email=data.assigned_to_email)
        except User.DoesNotExist:
            raise HTTPException(status_code=404, detail="Assignee email not found")

    task = Task.objects.create(
        title=data.title,
        description=data.description,
        priority=data.priority,
        due_date=data.due_date,
        created_by=current_user,
        assigned_to=assignee
    )

    if assignee and assignee != current_user:
        create_notification(
            recipient=assignee,
            message=f"{current_user.email} assigned you a task: {task.title}",
            type_choice="task",
            related_id=task.id
        )

    return task

# 3. UPDATE TASK 
@router.patch("/{task_id}", response_model=TaskRead)
def update_task(task_id: int, data: TaskUpdate, current_user: User = Depends(get_current_user)):
    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        raise HTTPException(status_code=404, detail="Task not found")

    if data.status: task.status = data.status
    if data.priority: task.priority = data.priority
    
    if data.assigned_to_email:
        try:
            new_assignee = User.objects.get(email=data.assigned_to_email)
            task.assigned_to = new_assignee
            
            create_notification(
                recipient=new_assignee,
                message=f"Task reassigned to you by {current_user.email}: {task.title}",
                type_choice="task",
                related_id=task.id
            )
        except User.DoesNotExist:
            pass 

    task.save()
    return task
# 4. EMAIL TO TASK 
@router.post("/from-email/{email_id}", response_model=TaskRead)
def create_task_from_email(email_id: int, current_user: User = Depends(get_current_user)):
    try:
        email = Email.objects.get(id=email_id)
    except Email.DoesNotExist:
        raise HTTPException(status_code=404, detail="Email not found")

    task = Task.objects.create(
        title=email.subject or f"Task from Email #{email.id}",
        description=email.body or "No content",
        created_by=current_user,
        email=email,
        priority="medium" 
    )
    return task