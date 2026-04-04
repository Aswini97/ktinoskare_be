from rest_framework import serializers
from .models import Pet

class PetSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    device_uid = serializers.ReadOnlyField(source='device.device_uid')

    class Meta:
        model = Pet
        fields = [
            'id', 'name', 'owner', 'device', 'device_uid', 
            'breed', 'species', 'gender', 'dob', 'age', 
            'weight', 'color', 'healthStatus', 'avatar', 
            'vaccinated', 'lastCheckup', 'nextCheckup', 'notes'
        ]