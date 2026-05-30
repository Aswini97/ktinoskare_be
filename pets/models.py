from django.db import models
from django.contrib.auth.models import User
from devices.models import Device

class Species(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Species"

    def __str__(self):
        return self.name

class PetBreed(models.Model):
    name = models.CharField(max_length=100, unique=True)
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name='breeds')
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

class Pet(models.Model):
    HEALTH_STATUS_CHOICES = [
        ('HEALTHY', 'Healthy'),
        ('SICK', 'Sick'),
        ('UNDER_TREATMENT', 'Under Treatment'),
        ('RECOVERING', 'Recovering'),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets')
    device = models.OneToOneField(Device, on_delete=models.SET_NULL, null=True, blank=True, related_name='pet')
    name = models.CharField(max_length=100)    
    species = models.ForeignKey(Species, on_delete=models.SET_NULL, null=True, blank=True, related_name='pets')
    breed = models.ForeignKey(PetBreed, on_delete=models.SET_NULL, null=True, blank=True, related_name='pets')
    gender = models.CharField(max_length=10, blank=True)
    dob = models.DateField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    color = models.CharField(max_length=100, blank=True)
    vaccinated = models.BooleanField(default=False)
    last_checkup = models.DateField(null=True, blank=True)
    next_checkup = models.DateField(null=True, blank=True)
    health_status = models.CharField(max_length=20, choices=HEALTH_STATUS_CHOICES, default='HEALTHY')
    notes = models.TextField(blank=True)
    avatar = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

class VetDoctor(models.Model):
    vet_name = models.CharField(max_length=255)
    designation = models.CharField(max_length=255)
    hospital_name = models.CharField(max_length=255)
    license_no = models.CharField(max_length=100, unique=True)
    rating = models.FloatField(default=5.0)

    def __str__(self):
        return f"Dr. {self.vet_name} ({self.hospital_name})"