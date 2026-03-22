from django.db import models
from devices.models import Device
# Create your models here.


class TelemetryRecord(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='telemetry')

    heart_rate = models.FloatField(null=True, blank=True)
    spo2 = models.FloatField(null=True, blank=True)

    ambient_temperature = models.FloatField(null=True, blank=True)
    object_temperature = models.FloatField(null=True, blank=True)

    accel_x = models.FloatField(null=True, blank=True)
    accel_y = models.FloatField(null=True, blank=True)
    accel_z = models.FloatField(null=True, blank=True)
    motion_detected = models.BooleanField(default=False)

    light_level = models.FloatField(null=True, blank=True)

    battery_voltage = models.FloatField(null=True, blank=True)
    battery_percentage = models.IntegerField(null=True, blank=True)

    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.device.device_uid} @ {self.created_at}"
