from django.db import models

# Create your models here.

class Device(models.Model):
    device_uid = models.CharField(max_length=100, unique=True)
    firmware_version = models.CharField(max_length=50)
    battery_level = models.FloatField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.device_uid