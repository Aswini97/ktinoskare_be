from rest_framework import serializers
from .models import *
from django.contrib.auth.models import User

class PetSerializer(serializers.ModelSerializer):
    # Maps the 'owner' model field to 'owner_id' in JSON
    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='owner'
    )
    owner_username = serializers.ReadOnlyField(source='owner.username')
    device_uid = serializers.ReadOnlyField(source='device.device_uid')
    species_name = serializers.ReadOnlyField(source='species.name')
    breed_name = serializers.ReadOnlyField(source='breed.name')

    class Meta:
        model = Pet
        fields = [
            'id', 'owner_id', 'owner_username', 'name', 'device', 'device_uid', 
            'species', 'species_name', 'breed', 'breed_name', 'gender', 
            'dob', 'weight', 'color', 'vaccinated', 'last_checkup', 
            'next_checkup', 'health_status', 'notes', 'avatar', 
            'created_at', 'updated_at', 'is_deleted', 'deleted_at'
        ]

class SpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Species
        fields = '__all__'

class PetBreedSerializer(serializers.ModelSerializer):
    species_name = serializers.ReadOnlyField(source='species.name')

    class Meta:
        model = PetBreed
        fields = ['id', 'name', 'species_id', 'species_name']