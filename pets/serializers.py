from rest_framework import serializers
from .models import Pet, Species, PetBread
from django.contrib.auth.models import User

class PetSerializer(serializers.ModelSerializer):
    # Maps the 'owner' model field to 'owner_id' in JSON
    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='owner'
    )
    owner_username = serializers.ReadOnlyField(source='owner.username')
    device_uid = serializers.ReadOnlyField(source='device.device_uid')
    species_name = serializers.ReadOnlyField(source='species_id.name')
    breed_name = serializers.ReadOnlyField(source='breed_id.name')

    class Meta:
        model = Pet
        fields = [
            'id', 'owner_id', 'owner_username', 'name', 'device', 'device_uid', 
            'species_id', 'species_name', 'breed_id', 'breed_name', 'gender', 
            'dob', 'weight', 'color', 'vaccinated', 'lastCheckup', 
            'nextCheckup', 'healthStatus', 'notes', 'avatar', 
            'created_at', 'updated_at'
        ]

class SpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Species
        fields = '__all__'

class PetBreadSerializer(serializers.ModelSerializer):
    # Maps 'species_id' for consistency
    species_name = serializers.ReadOnlyField(source='species_id.name')

    class Meta:
        model = PetBread
        fields = ['id', 'name', 'species_id', 'species_name']