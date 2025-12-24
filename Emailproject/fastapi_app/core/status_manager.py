from datetime import datetime
from typing import Optional
from asgiref.sync import sync_to_async
from django.contrib.auth import get_user_model
from fastapi_app.core.socket_manager import manager

User = get_user_model()

class StatusManager:
    
    PRIORITY_MAP = {
        'OFFLINE': 100,
        'DND': 90,       
        'IN_MEETING': 80,
        'BRB': 50,       
        'AWAY': 40,      
        'AVAILABLE': 0   
    }

    @staticmethod
    async def request_status_change(user_id: int, new_status: str, is_manual: bool = False):
        """
        The Master Async Function.
        1. Calls the DB (in a thread)
        2. If successful, Broadcasts (in the main loop)
        """
        success = await StatusManager._update_user_status(user_id, new_status, is_manual)

        if success:
            await manager.broadcast_to_all({ 
                "type": "USER_STATUS_UPDATE",
                "user_id": user_id,
                "status": new_status
            })

    @staticmethod
    @sync_to_async
    def _update_user_status(user_id: int, new_status: str, is_manual: bool):
        """
        Strictly Database Logic. No Async/WebSockets allowed here.
        """
        try:
            user = User.objects.get(id=user_id)
            current_status = user.current_status
            
            if current_status == 'OFFLINE' and new_status != 'AVAILABLE' and new_status != 'OFFLINE':
                print(f"🚫 Blocked: Cannot go from OFFLINE to {new_status}")
                return False

            if user.is_manually_set and user.current_status == 'DND' and not is_manual:
                print(f"🛡️ Blocked: User is on DND. Ignoring auto-update to {new_status}")
                return False

            if new_status == 'AVAILABLE' and current_status == 'IN_MEETING':
                pass
            
            user.current_status = new_status
            user.is_manually_set = is_manual
            
            if new_status in ['AVAILABLE', 'OFFLINE']:
                user.status_expiry = None
                user.status_message = None

            user.save()
            print(f"✅ Status Changed: {user.email} -> {new_status}")
            
            return True

        except User.DoesNotExist:
            return False