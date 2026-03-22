from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import TelemetryRecord, Device
from .serializers import TelemetryRecordSerializer


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

    # Custom route: /api/v1/telemetry/<device_id>/
    @action(detail=False, methods=["get"], url_path=r"(?P<device_id>\d+)")
    def by_device(self, request, device_id=None):
        try:
            device = Device.objects.get(pk=device_id)
        except Device.DoesNotExist:
            return Response({"error": "Device not found"}, status=404)

        records = TelemetryRecord.objects.filter(device=device).order_by("-created_at")
        serializer = self.get_serializer(records, many=True)
        return Response(serializer.data)