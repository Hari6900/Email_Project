from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password) 
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'ADMIN') 
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('MANAGER', 'Manager'),
        ('STAFF', 'Staff'),
    )
    
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, null=True)
    nationality = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='STAFF')

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Email(models.Model):
    sender = models.ForeignKey(User, related_name="sent_emails", on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name="received_emails", on_delete=models.CASCADE, null=True, 
    blank=True)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    parent = models.ForeignKey("self", null=True, blank=True, related_name="replies", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    is_deleted_by_sender = models.BooleanField(default=False)
    
    is_deleted_by_receiver = models.BooleanField(default=False)

    is_important = models.BooleanField(default=False) 
    is_favorite = models.BooleanField(default=False)  
    is_archived = models.BooleanField(default=False)
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
        Email, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name="chat_room"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or f"Room {self.id}"

class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, related_name="messages", on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name="sent_chat_messages", on_delete=models.CASCADE)
    
    content = models.TextField(blank=True, null=True) 
    attachment = models.FileField(upload_to='chat_attachments/', blank=True, null=True) 
    
    timestamp = models.DateTimeField(auto_now_add=True)

    read_by = models.ManyToManyField(User, related_name="read_messages", blank=True)
    starred_by = models.ManyToManyField(User, related_name="starred_chat_messages", blank=True)
    def __str__(self):
        return f"{self.sender.email}: {self.content[:20]}"    

class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.ForeignKey(Email, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(
        max_length=20,
        choices=[
            ("todo", "To Do"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
        ],
        default="todo"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
