from django.utils.dateparse import parse_datetime
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
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
    list=extend_schema(
        tags=["Telemetry"], 
        description="Retrieve history. Use ?user_id=X to filter.",
        parameters=[OpenApiParameter("user_id", type=int)]
    ),
    retrieve=extend_schema(tags=["Telemetry"], description="Retrieve a specific record.")
)
class TelemetryRecordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TelemetryRecordSerializer
    permission_classes = [permissions.AllowAny] # No Auth
    pagination_class = TelemetryPagination

    def get_queryset(self):
        queryset = TelemetryRecord.objects.all().order_by("-created_at")
        user_id = self.request.query_params.get('user_id')
        
        if user_id:
            return queryset.filter(device__pet__owner=user_id)
        return queryset

    @action(detail=False, methods=["get"], url_path=r"device/(?P<device_id>\d+)")
    def by_device(self, request, device_id=None):
        try:
            device = Device.objects.get(pk=device_id)
        except Device.DoesNotExist:
            return Response({"error": "Device not found"}, status=status.HTTP_404_NOT_FOUND)

        qs = TelemetryRecord.objects.filter(device=device).order_by("-created_at")

        # Date Filtering
        from_date = request.query_params.get("from")
        to_date = request.query_params.get("to")
        if from_date:
            dt = parse_datetime(from_date)
            if dt: qs = qs.filter(created_at__gte=dt)
        if to_date:
            dt = parse_datetime(to_date)
            if dt: qs = qs.filter(created_at__lte=dt)

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)