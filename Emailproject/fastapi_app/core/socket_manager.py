from fastapi import WebSocket
from typing import List, Dict
from django.utils import timezone
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.user_connection_counts: Dict[int, int] = {} 

    async def connect(self, websocket: WebSocket, room_id: int, user_id: int):
        await websocket.accept()
        
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)
        self.user_connection_counts[user_id] = self.user_connection_counts.get(user_id, 0) + 1
        
        await self.broadcast({
            "type": "USER_STATUS",
            "user_id": user_id,
            "status": "online"
        }, room_id)

    async def disconnect(self, websocket: WebSocket, room_id: int, user_id: int):
        if room_id in self.active_connections:
            if websocket in self.active_connections[room_id]:
                self.active_connections[room_id].remove(websocket)
                
        if user_id in self.user_connection_counts:
            self.user_connection_counts[user_id] -= 1
            
            if self.user_connection_counts[user_id] <= 0:
                del self.user_connection_counts[user_id]
                
                await self.update_last_seen(user_id)

        await self.broadcast({
            "type": "USER_STATUS",
            "user_id": user_id,
            "status": "offline"
        }, room_id)

    @sync_to_async
    def update_last_seen(self, user_id: int):
        try:
            user = User.objects.get(id=user_id)
            user.last_seen = timezone.now()
            user.save()
            print(f"🕒 Updated Last Seen for {user.email}")
        except User.DoesNotExist:
            pass

    async def broadcast(self, message: dict, room_id: int):
        """Send a message to everyone in the room"""
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id][:]:
                try:
                    await connection.send_json(message)
                except:
                    pass

    def get_online_users(self) -> List[int]:
        """Returns a list of User IDs that are currently connected."""
        return list(self.user_connection_counts.keys())
    
    async def broadcast_to_all(self, message: dict):
        """
        Send a message to EVERY connected user in ALL rooms.
        Used for Status Updates (Online/Offline/In Meeting).
        """
        for room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

manager = ConnectionManager()

    