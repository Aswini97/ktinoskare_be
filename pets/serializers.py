from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Pet, Species, PetBreed
from devices.models import DeviceMaster, UserDeviceMapping


class PetSerializer(serializers.ModelSerializer):
    owner_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='owner'
    )
    owner_username = serializers.ReadOnlyField(source='owner.username')

    # Accepts device primary key (e.g. 1) to link, or null to unlink
    device = serializers.PrimaryKeyRelatedField(
        queryset=DeviceMaster.objects.filter(is_active=True),
        required=False,
        allow_null=True
    )
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

    def validate(self, attrs):
        # 1. Resolve owner from payload or existing record
        owner = attrs.get('owner') or (self.instance.owner if self.instance else None)

        # 2. Process device attachment or removal
        if 'device' in attrs:
            device = attrs.get('device')

            # Passing null unlinks the device from this pet
            if device is None:
                return attrs

            # Validation Rule 1: Ensure the user owns this device
            if owner:
                is_owned = UserDeviceMapping.objects.filter(
                    user=owner,
                    device=device,
                    is_active=True
                ).exists()

                if not is_owned:
                    raise serializers.ValidationError({
                        "device": f"You do not own device '{device.device_uid}'. Register it to your account first."
                    })

            # Validation Rule 2: Ensure device is not already worn by another pet
            attached_pet_query = Pet.objects.filter(device=device, is_deleted=False)
            if self.instance:
                attached_pet_query = attached_pet_query.exclude(id=self.instance.id)

            attached_pet = attached_pet_query.first()
            if attached_pet:
                raise serializers.ValidationError({
                    "device": f"Device '{device.device_uid}' is already linked to '{attached_pet.name}'."
                })

        return attrs


class SpeciesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Species
        fields = '__all__'


class PetBreedSerializer(serializers.ModelSerializer):
    species_id = serializers.PrimaryKeyRelatedField(
        queryset=Species.objects.filter(is_deleted=False),
        source='species'
    )
    species_name = serializers.ReadOnlyField(source='species.name')

    class Meta:
        model = PetBreed
        fields = ['id', 'name', 'species_id', 'species_name']
