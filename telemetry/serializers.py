from rest_framework import serializers
from .models import TelemetryRecord

# Use this for raw history logs
class TelemetryRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelemetryRecord
        fields = "__all__"

# Specialized serializers for aggregated dashboard data
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