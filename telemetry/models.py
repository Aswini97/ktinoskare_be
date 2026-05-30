from django.contrib.gis.db import models
from devices.models import Device

class TelemetryRecord(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='telemetry')
    
    # Metadata
    is_emergency = models.BooleanField(default=False)
    window_seconds = models.IntegerField(default=30)
    
    # Heart Rate Parameters (BPM)
    avg_heart_rate = models.FloatField(null=True, blank=True)
    min_heart_rate = models.FloatField(null=True, blank=True)
    max_heart_rate = models.FloatField(null=True, blank=True)

    # SpO2 Parameters (%)
    avg_spo2 = models.FloatField(null=True, blank=True)
    min_spo2 = models.FloatField(null=True, blank=True)
    max_spo2 = models.FloatField(null=True, blank=True)

    # Temperature Parameters (°C)
    avg_ambient_temp = models.FloatField(null=True, blank=True)
    avg_object_temp = models.FloatField(null=True, blank=True)
    max_object_temp = models.FloatField(null=True, blank=True)

    # Physical Motion Sensors
    accel_x = models.FloatField(null=True, blank=True)
    accel_y = models.FloatField(null=True, blank=True)
    accel_z = models.FloatField(null=True, blank=True)
    motion_detected = models.BooleanField(default=False)
    light_level = models.FloatField(null=True, blank=True)

    # Power Metrics
    battery_voltage = models.FloatField(null=True, blank=True)
    battery_percentage = models.IntegerField(null=True, blank=True)

    # --- UPGRADED SPATIAL REPRESENTATION ---
    location = models.PointField(srid=4326)

    # Environmental Context
    temp_dht22 = models.FloatField(null=True, blank=True)
    humidity = models.FloatField(null=True, blank=True)
    heat_index = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField() # Hypertable chunk partition coordinate tracking axis

    class Meta:
        db_table = 'tracker_telemetryrecord'
        ordering = ['-created_at']

    def __str__(self):
        status = "🚨 ALERT" if self.is_emergency else "Normal"
        return f"{self.device.device_uid} [{status}] @ {self.created_at}"