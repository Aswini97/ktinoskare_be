from django.db import models
from django.contrib.auth.models import User
from devices.models import Device

class Species(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class PetBread(models.Model):
    name = models.CharField(max_length=100, unique=True)
    species_id = models.ForeignKey(Species, on_delete=models.CASCADE, related_name='breeds')

    def __str__(self):
        return self.name

class Pet(models.Model):
    HEALTH_STATUS_CHOICES = [
        ('Healthy', 'Healthy'),
        ('Sick', 'Sick'),
        ('Under Treatment', 'Under Treatment'),
        ('Recovering', 'Recovering'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets')
    device = models.OneToOneField(Device, on_delete=models.SET_NULL, null=True, blank=True, related_name='pet')
    name = models.CharField(max_length=100)    
    species_id = models.ForeignKey(Species, on_delete=models.SET_NULL, null=True, blank=True, related_name='pets')
    breed_id = models.ForeignKey(PetBread, on_delete=models.SET_NULL, null=True, blank=True, related_name='pets')
    gender = models.CharField(max_length=10, blank=True)
    dob = models.DateField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    color = models.CharField(max_length=100, blank=True)
    vaccinated = models.BooleanField(default=False)
    lastCheckup = models.DateField(null=True, blank=True)
    nextCheckup = models.DateField(null=True, blank=True)
    healthStatus = models.CharField(max_length=20, choices=HEALTH_STATUS_CHOICES, default='Healthy')
    notes = models.TextField(blank=True)
    avatar = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name