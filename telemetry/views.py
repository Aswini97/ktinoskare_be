from rest_framework import viewsets
from .models import TelemetryRecord
from .serializers import TelemetryRecordSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(tags=["Telemetry"], description="Retrieve a list of all telemetry records."),
    retrieve=extend_schema(tags=["Telemetry"], description="Retrieve details of a specific telemetry record by its ID."),
    create=extend_schema(tags=["Telemetry"], description="Create a new telemetry record."),
    update=extend_schema(tags=["Telemetry"], description="Update an existing telemetry record."),
    partial_update=extend_schema(tags=["Telemetry"], description="Partially update an existing telemetry record."),
    destroy=extend_schema(tags=["Telemetry"], description="Delete a telemetry record.")
)
class TelemetryRecordViewSet(viewsets.ModelViewSet):
    queryset = TelemetryRecord.objects.all()
    serializer_class = TelemetryRecordSerializer
