from rest_framework import serializers
from .models import *

class PetSerializer(serializers.ModelSerializer):
    owner_username = serializers.ReadOnlyField(source='owner.username')
    device_uid = serializers.ReadOnlyField(source='device.device_uid')
    breed_name = serializers.ReadOnlyField(source='breedId.name')

    class Meta:
        model = Pet
        # Include 'owner' here so it is writable
        fields = [
            'id', 'owner', 'owner_username', 'name', 'device', 'device_uid', 
            'breedId', 'breed_name', 'species', 'gender', 'dob', 'age', 
            'weight', 'color', 'vaccinated', 'lastCheckup', 'nextCheckup', 
            'healthStatus', 'notes', 'avatar', 'created_at', 'updated_at'
        ]

class SpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Species
        fields = '__all__'

class PetBreadSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = PetBread
        fields = ['id', 'name', 'category', 'category_name']