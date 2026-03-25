from django.utils.dateparse import parse_datetime
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import TelemetryRecord, Device
from .serializers import TelemetryRecordSerializer


@extend_schema_view(
    list=extend_schema(tags=["Telemetry"], description="Retrieve all telemetry records."),
    retrieve=extend_schema(tags=["Telemetry"], description="Retrieve a telemetry record by ID."),
    create=extend_schema(tags=["Telemetry"], description="Create a new telemetry record."),
    update=extend_schema(tags=["Telemetry"], description="Update an existing telemetry record."),
    partial_update=extend_schema(tags=["Telemetry"], description="Partially update a telemetry record."),
    destroy=extend_schema(tags=["Telemetry"], description="Delete a telemetry record."),
)
class TelemetryRecordViewSet(viewsets.ModelViewSet):
    queryset = TelemetryRecord.objects.all()
    serializer_class = TelemetryRecordSerializer

    # GET /api/v1/telemetry/<device_id>/?from=2026-03-01T00:00:00&to=2026-03-08T23:59:59&page=2&page_size=20
    @action(detail=False, methods=["get"], url_path=r"(?P<device_id>\d+)")
    def by_device(self, request, device_id=None):
        try:
            device = Device.objects.get(pk=device_id)
        except Device.DoesNotExist:
            return Response({"error": "Device not found"}, status=404)

        qs = TelemetryRecord.objects.filter(device=device).order_by("-created_at")

        # Optional date range filters
        from_date = request.query_params.get("from")
        to_date = request.query_params.get("to")

        if from_date:
            from_dt = parse_datetime(from_date)
            if from_dt:
                qs = qs.filter(created_at__gte=from_dt)
        if to_date:
            to_dt = parse_datetime(to_date)
            if to_dt:
                qs = qs.filter(created_at__lte=to_dt)

        # Apply pagination
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)