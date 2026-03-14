from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class PetCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class PetBread(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(PetCategory, on_delete=models.CASCADE, related_name='breeds')

    def __str__(self):
        return self.name

class Pet(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pets')
    name = models.CharField(max_length=100)
    breed = models.ForeignKey(PetBread, on_delete=models.SET_NULL, null=True, blank=True, related_name='pets')
    gender = models.CharField(max_length=10, blank=True)
    dob = models.DateField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
