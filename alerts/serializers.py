from rest_framework import serializers
from .models import Alert

class AlertSerializer(serializers.ModelSerializer):
    device_uid = serializers.ReadOnlyField(source='device.device_uid')
    pet_name = serializers.ReadOnlyField(source='device.pet.name')

    class Meta:
        model = Alert
        fields = [
            'id', 'device', 'device_uid', 'pet_name', 
            'alert_type', 'message', 'is_resolved', 'created_at'
        ]