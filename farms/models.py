from django.contrib.gis.db import models
from django.contrib.auth.models import User

class Farm(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_farms')
    location_name = models.CharField(max_length=255)
    total_area = models.FloatField()
    geo_center = models.PointField(srid=4326)   # Spatial center tracking point
    boundary = models.PolygonField(srid=4326) # Spatial geofence containment boundary polygon
    head_count = models.IntegerField(default=0)
    cow_count = models.IntegerField(default=0)

    def __str__(self):
        return self.location_name

class FarmManagerMapping(models.Model):
    farm = models.ForeignKey(Farm, on_delete=models.CASCADE, related_name='manager_mappings')
    manager = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_farms')
    is_on_duty = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.manager.username} -> {self.farm.location_name} (On Duty: {self.is_on_duty})"