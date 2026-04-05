from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Device(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices', null=True, blank=True, default=1)
    device_uid = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    firmware_version = models.CharField(max_length=50, blank=True, null=True)

    battery_level = models.FloatField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    registered_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.device_uid} ({self.name or 'Unnamed'})"