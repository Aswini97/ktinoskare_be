from rest_framework import viewsets
from .models import TelemetryRecord
from .serializers import TelemetryRecordSerializer


class TelemetryRecordViewSet(viewsets.ModelViewSet):
    queryset = TelemetryRecord.objects.all()
    serializer_class = TelemetryRecordSerializer
