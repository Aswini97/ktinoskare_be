from django.db import models
from django.contrib.auth.models import User

class DeviceMaster(models.Model):
    """Factory inventory table: Holds standalone hardware specifications only."""
    device_uid = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    sim_iccid = models.CharField(max_length=22, unique=True, blank=True, null=True)
    firmware_version = models.CharField(max_length=50, blank=True, null=True)
    hardware_version = models.CharField(max_length=50, blank=True, null=True)
    checksum = models.CharField(max_length=64, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.device_uid} - {self.name or 'Unnamed Master'}"

Device = DeviceMaster


class UserDeviceMapping(models.Model):
    """Mapping table: Links a registered physical device to an owner account."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_mappings')
    device = models.OneToOneField(
        DeviceMaster,
        on_delete=models.CASCADE,
        related_name='user_mapping',
        to_field='device_uid'
    )
    custom_name = models.CharField(max_length=255, blank=True, null=True)
    battery_level = models.FloatField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'device')

    def __str__(self):
        return f"{self.user.username} -> {self.device.device_uid} ({self.custom_name or 'No Nickname'})"