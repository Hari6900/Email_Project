from celery import shared_task
from django.contrib.auth import get_user_model
import redis
import json

User = get_user_model()

@shared_task
def reset_user_status(user_id: int):
    """
    Auto-reset task that also broadcasts the update via WebSockets.
    """
    try:
        user = User.objects.get(id=user_id)
        
        if user.current_status == 'OFFLINE':
            print(f"User {user.email} is OFFLINE. Skipping auto-reset.")
            return

        print(f"Time is up! Resetting {user.email} to AVAILABLE.")
        
        user.current_status = 'AVAILABLE'
        user.status_message = None
        user.status_expiry = None
        user.is_manually_set = False
        user.save()

        try:
            r = redis.Redis(host='localhost', port=6379, db=0)
            
            message = {
                "type": "USER_STATUS_UPDATE",
                "user_id": user.id,
                "status": "AVAILABLE",
                "message": None
            }
            r.publish("status_updates", json.dumps(message))
            print(f"Published update to Redis for {user.email}")
            
        except Exception as e:
            print(f"Failed to publish to Redis: {e}")
        
    except User.DoesNotExist:
        print(f"User {user_id} not found during auto-reset.")