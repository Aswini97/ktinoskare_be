from rest_framework import serializers
from .models import Device

class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = '__all__'

class DeviceRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = [
            'device_uid',
            'name',
            'sim_iccid',
            'firmware_version',
            'hardware_version',
            'checksum',
            'is_active'
        ]

    def validate_device_uid(self, value):
        if Device.objects.filter(device_uid=value).exists():
            raise serializers.ValidationError(f"Device with UID '{value}' already exists.")
        return value