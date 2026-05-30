from django.db import models
from django.contrib.auth.models import User

class UserAccount(models.Model):
    ROLE_CHOICES = [
        ('OWNER', 'Owner'),
        ('MANAGER', 'Manager'),
        ('CARETAKER', 'Caretaker'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='OWNER')
    emergency_contact = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.role})"