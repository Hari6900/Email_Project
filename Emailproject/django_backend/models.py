from django.db import models
from django.utils import timezone
from django.conf import settings
from django.utils.timezone import now
from django.contrib.auth.models import AbstractUser



class User(AbstractUser):
    email = models.EmailField(unique=True)
    mobile_number = models.CharField(max_length=15, unique=True, null=True, blank=True)

    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_expires_at = models.DateTimeField(null=True, blank=True)

    last_seen = models.DateTimeField(null=True, blank=True)

    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('IN_MEETING', 'In Meeting'),
        ('DND', 'Do Not Disturb'),
        ('BRB', 'Be Right Back'),
        ('AWAY', 'Appear Away'),
        ('OFFLINE', 'Offline'),
    )

    current_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='OFFLINE'
    )
    is_manually_set = models.BooleanField(default=False)
    status_expiry = models.DateTimeField(null=True, blank=True)
    status_message = models.CharField(max_length=255, blank=True, null=True)
    last_active_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.email or self.username

class Email(models.Model):
    sender = models.ForeignKey(User, related_name="sent_emails", on_delete=models.CASCADE)
    receiver = models.ForeignKey(
        User, related_name="received_emails",
        on_delete=models.CASCADE, null=True, blank=True
    )
    subject = models.CharField(max_length=255)
    body = models.TextField()
    parent = models.ForeignKey("self", null=True, blank=True, related_name="replies", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    is_deleted_by_sender = models.BooleanField(default=False)
    is_deleted_by_receiver = models.BooleanField(default=False)
    is_important = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    is_spam = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)

    STATUS_CHOICES = (
        ('DRAFT', 'Draft'),
        ('SENT', 'Sent')
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='SENT')

    def __str__(self):
        receiver_email = self.receiver.email if self.receiver else "Draft"
        return f"{self.sender.email} -> {receiver_email}"


class Attachment(models.Model):
    email = models.ForeignKey(Email, related_name="attachments", on_delete=models.CASCADE)
    file = models.FileField(upload_to='attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for Email {self.email.id}"


class ChatRoom(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    is_group = models.BooleanField(default=False)
    participants = models.ManyToManyField(User, related_name="chat_rooms")
    related_email = models.OneToOneField(
        Email, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="chat_room"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"Room {self.id}"


class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, related_name="messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name="sent_chat_messages", on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    content = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='chat_attachments/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    read_by = models.ManyToManyField(User, related_name="read_messages", blank=True)
    starred_by = models.ManyToManyField(User, related_name="starred_chat_messages", blank=True)
    mentions = models.ManyToManyField(User, related_name="mentioned_in_messages", blank=True)

    is_deleted = models.BooleanField(default=False)
    is_forwarded = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.email}: {self.content[:20]}"


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default="#FFFFFF")

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey(User, related_name="owned_projects", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, related_name="created_tasks", on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(
        User, related_name="assigned_tasks",
        null=True, blank=True, on_delete=models.SET_NULL
    )
    due_date = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name="tasks", blank=True)
    project = models.ForeignKey(Project, related_name="tasks", on_delete=models.CASCADE, null=True, blank=True)
    priority = models.CharField(
        max_length=10,
        choices=(("low","Low"),("medium","Medium"),("high","High")),
        default="medium"
    )
    email = models.ForeignKey(Email, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(
        max_length=20,
        choices=(("todo","To Do"),("in_progress","In Progress"),("done","Done")),
        default="todo"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# =========================
# REMAINING MODELS
# (UNCHANGED – SAFE)
# =========================
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    full_name = models.CharField(max_length=150)
    display_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    language = models.CharField(max_length=30, default="English")
    date_format = models.CharField(max_length=20, default="DD-MM-YYYY")
    store_activity = models.BooleanField(default=True)
    is_2fa_enabled = models.BooleanField(default=False)
    two_factor_secret = models.CharField(max_length=32, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class LoginActivity(models.Model):
    user = models.ForeignKey(User, related_name="login_activities", on_delete=models.CASCADE)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)


class DriveFile(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="drive_files")
    original_name = models.CharField(max_length=255)
    file = models.FileField(upload_to="drive/")
    size = models.BigIntegerField(default=0)
    content_type = models.CharField(max_length=100, default="application/octet-stream")
    uploaded_at = models.DateTimeField(default=now)
    created_at = models.DateTimeField(auto_now_add=True)
