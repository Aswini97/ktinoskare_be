from django.db import models
from devices.models import Device

class Alert(models.Model):
    ALERT_TYPES = (
        ('LOW_TEMP', 'Low Temperature Exception'),
        ('HIGH_TEMP', 'High Temperature Exception'),
        ('LOW_BATTERY', 'Low Battery Warning'),
        ('ABNORMAL_HR', 'Abnormal Heart Rate'),
        ('GEOFENCE_BREACH', 'Geofence Exit Breach'),
        ('GEOFENCE_ENTRY', 'Geofence Entry'),
    )
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.alert_type}] {self.device.device_uid}: {self.message}"