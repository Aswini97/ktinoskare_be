from django.db import models
from devices.models import Device

class TelemetryRecord(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='telemetry')
    
    # Metadata
    is_emergency = models.BooleanField(default=False)
    window_seconds = models.IntegerField(default=30) # Tracking the averaging window
    
    # Heart Rate (BPM)
    avg_heart_rate = models.FloatField(null=True, blank=True)
    min_heart_rate = models.FloatField(null=True, blank=True)
    max_heart_rate = models.FloatField(null=True, blank=True)

    # SpO2 (%)
    avg_spo2 = models.FloatField(null=True, blank=True)
    min_spo2 = models.FloatField(null=True, blank=True)
    max_spo2 = models.FloatField(null=True, blank=True)

    # Temperature (°C)
    avg_ambient_temp = models.FloatField(null=True, blank=True)
    avg_object_temp = models.FloatField(null=True, blank=True)
    max_object_temp = models.FloatField(null=True, blank=True) # Critical for alerts

    # Movement & Environment
    accel_x = models.FloatField(null=True, blank=True)
    accel_y = models.FloatField(null=True, blank=True)
    accel_z = models.FloatField(null=True, blank=True)
    motion_detected = models.BooleanField(default=False)
    light_level = models.FloatField(null=True, blank=True)

    # Power
    battery_voltage = models.FloatField(null=True, blank=True)
    battery_percentage = models.IntegerField(null=True, blank=True)

    # Location (Stored as CharField to maintain precision)
    latitude = models.CharField(max_length=25, default="0.0")
    longitude = models.CharField(max_length=25, default="0.0")

    # Humidity
    temp_dht22 = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    heat_index = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "🚨 ALERT" if self.is_emergency else "Normal"
        return f"{self.device.device_uid} [{status}] @ {self.created_at}"