from rest_framework import serializers
from .models import DeviceMaster, UserDeviceMapping

class DeviceMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceMaster
        fields = '__all__'


class UserDeviceMappingSerializer(serializers.ModelSerializer):
    device_uid = serializers.SlugRelatedField(
        slug_field='device_uid',
        queryset=DeviceMaster.objects.all(),
        source='device'
    )
    hardware_info = DeviceMasterSerializer(source='device', read_only=True)

    class Meta:
        model = UserDeviceMapping
        fields = [
            'id',
            'user',
            'device_uid',
            'custom_name',
            'battery_level',
            'last_seen',
            'is_active',
            'assigned_at',
            'hardware_info'
        ]