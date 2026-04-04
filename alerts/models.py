from django.db import models
from devices.models import Device

class Alert(models.Model):
    ALERT_TYPES = (
        ('high_temperature', 'High Temperature'),
        ('low_battery', 'Low Battery'),
        ('abnormal_heart_rate', 'Abnormal Heart Rate'),
        ('geofence_breach', 'Geofence Breach'),
    )
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=50, choices=ALERT_TYPES)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.alert_type}] {self.device.device_uid}: {self.message}"