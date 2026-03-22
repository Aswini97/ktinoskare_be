from django.db import models

# Create your models here.

class Device(models.Model):
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