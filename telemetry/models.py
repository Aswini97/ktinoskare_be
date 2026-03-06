from django.db import models
from devices.models import Device
# Create your models here.


class TelemetryRecord(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='telemetry')
    heart_rate = models.FloatField(null=True, blank=True)
    temperature = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    motion = models.IntegerField(null=True, blank=True)
    battery_level = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.device.device_uid} @ {self.created_at}"
