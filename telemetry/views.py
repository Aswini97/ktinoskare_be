from django.utils.dateparse import parse_datetime
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.pagination import PageNumberPagination

from .models import TelemetryRecord, Device
from .serializers import TelemetryRecordSerializer

class TelemetryPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "total_pages": self.page.paginator.num_pages,
            "current_page": self.page.number,
            "results": data
        })

@extend_schema_view(
    list=extend_schema(tags=["Telemetry"], description="Retrieve telemetry history for all your pets."),
    retrieve=extend_schema(tags=["Telemetry"], description="Retrieve a specific health record.")
)
class TelemetryRecordViewSet(viewsets.ReadOnlyModelViewSet): # Use ReadOnly to prevent manual POSTs
    serializer_class = TelemetryRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = TelemetryPagination

    def get_queryset(self):
        """
        Security: Only allow users to see telemetry for devices linked to THEIR pets.
        """
        return TelemetryRecord.objects.filter(
            device__pet__owner=self.request.user
        ).order_by("-created_at")

    @action(detail=False, methods=["get"], url_path=r"device/(?P<device_id>\d+)")
    def by_device(self, request, device_id=None):
        # 1. Ownership Check: Verify this device belongs to the user's pet
        try:
            device = Device.objects.get(pk=device_id, pet__owner=request.user)
        except Device.DoesNotExist:
            return Response({"error": "Device not found or access denied"}, status=status.HTTP_404_NOT_FOUND)

        # 2. Filter records
        qs = TelemetryRecord.objects.filter(device=device).order_by("-created_at")

        # 3. Date Filtering
        from_date = request.query_params.get("from")
        to_date = request.query_params.get("to")

        if from_date:
            from_dt = parse_datetime(from_date)
            if from_dt: qs = qs.filter(created_at__gte=from_dt)
        if to_date:
            to_dt = parse_datetime(to_date)
            if to_dt: qs = qs.filter(created_at__lte=to_dt)

        # 4. Paginate and Return
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)