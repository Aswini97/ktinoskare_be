from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class UserAccount(models.Model):
    # associates with Django's built-in User model
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.username
