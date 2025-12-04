from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, File, UploadFile
from django.core.files.base import ContentFile
from typing import List
from django.contrib.auth import get_user_model
from asgiref.sync import sync_to_async

from django_backend.models import ChatRoom, ChatMessage
from fastapi_app.schemas.chat_schemas import ChatRoomCreate, ChatRoomRead, MessageRead
from fastapi_app.core.socket_manager import manager
from fastapi_app.dependencies.auth import get_current_user

router = APIRouter()
User = get_user_model()

# REST API (The Paperwork)
@router.post("/rooms", response_model=ChatRoomRead)
def create_room(data: ChatRoomCreate, current_user: User = Depends(get_current_user)):
    room = ChatRoom.objects.create(
        name=data.name,
        is_group=data.is_group
    )
    
    participants = list(data.participant_emails)
    if current_user.email not in participants:
        participants.append(current_user.email)
        
    for email in participants:
        try:
            u = User.objects.get(email=email)
            room.participants.add(u)
        except User.DoesNotExist:
            continue 
            
    return format_room_response(room)

@router.get("/rooms", response_model=List[ChatRoomRead])
def list_rooms(current_user: User = Depends(get_current_user)):
    rooms = current_user.chat_rooms.all().order_by("-created_at")
    return [format_room_response(r) for r in rooms]

@router.get("/rooms/{room_id}/messages", response_model=List[MessageRead])
def get_messages(room_id: int, current_user: User = Depends(get_current_user)):
    
    try:
        room = ChatRoom.objects.get(id=room_id)
        if current_user not in room.participants.all():
             raise HTTPException(status_code=403, detail="Not a participant")
    except ChatRoom.DoesNotExist:
        raise HTTPException(status_code=404, detail="Room not found")

    msgs = room.messages.all().order_by("timestamp")
    
    return [
        {
            "id": m.id,
            "sender_email": m.sender.email,
            "content": m.content,
            "attachment_url": m.attachment.url if m.attachment else None,
            "timestamp": m.timestamp,
            "read_count": m.read_by.count()
        }
        for m in msgs
    ]

def format_room_response(room):
    
    last_msg_obj = room.messages.order_by("-timestamp").first()
    last_msg = None
    if last_msg_obj:
        last_msg = {
            "id": last_msg_obj.id,
            "sender_email": last_msg_obj.sender.email,
            "content": last_msg_obj.content,
            "timestamp": last_msg_obj.timestamp
        }

    return {
        "id": room.id,
        "name": room.name,
        "is_group": room.is_group,
        "participants": [u.email for u in room.participants.all()],
        "last_message": last_msg
    }

# FILE UPLOAD 
@router.post("/rooms/{room_id}/upload")
async def upload_chat_attachment(
    room_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    @sync_to_async
    def save_attachment_to_db():
        try:
            room = ChatRoom.objects.get(id=room_id)
            if current_user not in room.participants.all():
                raise PermissionError("Not a participant")
            
            file_content = file.file.read()
            
            msg = ChatMessage.objects.create(
                room=room,
                sender=current_user,
                content=f"Sent a file: {file.filename}", 
                attachment=None 
            )
        
            msg.attachment.save(file.filename, ContentFile(file_content))
            msg.save()
            return msg, room
        except ChatRoom.DoesNotExist:
            return None, None

    try:
        msg_obj, room = await save_attachment_to_db()
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not a participant")
        
    if not msg_obj:
        raise HTTPException(status_code=404, detail="Room not found")

    socket_message = {
        "id": msg_obj.id,
        "sender": current_user.email,
        "content": msg_obj.content,
        "attachment_url": msg_obj.attachment.url, 
        "timestamp": str(msg_obj.timestamp)
    }
    
    await manager.broadcast(socket_message, room_id)

    return {"message": "File uploaded", "url": msg_obj.attachment.url}

# WEBSOCKET (The Live Line)
@router.websocket("/ws/{room_id}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int, user_id: int):
    await manager.connect(websocket, room_id, user_id)
    
    @sync_to_async
    def save_message(room_id, user_id, content):
        room = ChatRoom.objects.get(id=room_id)
        sender = User.objects.get(id=user_id)
        msg = ChatMessage.objects.create(room=room, sender=sender, content=content)
        return msg, sender.email

    try:
        while True:
            data = await websocket.receive_text()
            msg_obj, sender_email = await save_message(room_id, user_id, data)
    
            response = {
                "id": msg_obj.id,
                "sender": sender_email,
                "content": data,
                "timestamp": str(msg_obj.timestamp)
            }
            await manager.broadcast(response, room_id)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id, user_id)