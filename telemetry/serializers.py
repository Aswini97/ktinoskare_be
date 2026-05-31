from rest_framework import serializers
from .models import TelemetryRecord

class TelemetryRecordSerializer(serializers.ModelSerializer):
    """
    Production-optimized serializer converting PostGIS binary geometry 
    primitives seamlessly into standard frontend JSON latitude/longitude parameters.
    """
    latitude = serializers.SerializerMethodField()
    longitude = serializers.SerializerMethodField()
    device_uid = serializers.CharField(source='device.device_uid', read_only=True)

    class Meta:
        model = TelemetryRecord
        exclude = ['location'] 

    def get_latitude(self, obj):
        return obj.location.y if obj.location else None

    def get_longitude(self, obj):
        return obj.location.x if obj.location else None

class HeartRateStatSerializer(serializers.Serializer):
    avg_heart_rate = serializers.FloatField()
    min_heart_rate = serializers.FloatField()
    max_heart_rate = serializers.FloatField()
    date = serializers.DateField()

class SpO2StatSerializer(serializers.Serializer):
    avg_spo2 = serializers.FloatField()
    min_spo2 = serializers.FloatField()
    max_spo2 = serializers.FloatField()
    date = serializers.DateField()

class TemperatureStatSerializer(serializers.Serializer):
    avg_temp = serializers.FloatField()
    max_temp = serializers.FloatField()
    date = serializers.DateField()

class AccelStatSerializer(serializers.Serializer):
    x = serializers.FloatField()
    y = serializers.FloatField()
    z = serializers.FloatField()
    date = serializers.DateField()

class EnvironmentalStatSerializer(serializers.Serializer):
    avg_temp = serializers.FloatField()
    avg_humidity = serializers.FloatField()
    avg_heat_index = serializers.FloatField()
    date = serializers.DateField()