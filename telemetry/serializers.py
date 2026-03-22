from rest_framework import serializers
from .models import TelemetryRecord


class TelemetryRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelemetryRecord
        fields = "__all__"