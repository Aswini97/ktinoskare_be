from django.utils.dateparse import parse_datetime
from django.db.models import Avg, Min, Max
from django.db.models.functions import TruncDate
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
        # Includes from/to range in history API responses
        return Response({
            "from": self.request.query_params.get("from"),
            "to": self.request.query_params.get("to"),
            "count": self.page.paginator.count,
            "total_pages": self.page.paginator.num_pages,
            "current_page": self.page.number,
            "results": data
        })

@extend_schema_view(
    list=extend_schema(
        tags=["Telemetry"], 
        description="Raw history logs. Use ?owner_id=X to filter.",
        parameters=[OpenApiParameter("owner_id", type=int)]
    )
)
class TelemetryRecordViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TelemetryRecordSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = TelemetryPagination

    def get_queryset(self):
        queryset = TelemetryRecord.objects.all().order_by("-created_at")
        owner_id = self.request.query_params.get('owner_id')
        if owner_id:
            return queryset.filter(device__pet__owner=owner_id)
        return queryset

    @extend_schema(
        tags=["Telemetry"],
        description="CHART DATA: Returns daily averages for all metrics in one call.",
        parameters=[
            OpenApiParameter("from", type=str, description="YYYY-MM-DD"),
            OpenApiParameter("to", type=str, description="YYYY-MM-DD")
        ]
    )
    @action(detail=False, methods=["get"], url_path=r"charts/(?P<device_id>\d+)")
    def chart_data(self, request, device_id=None):
        from_date = request.query_params.get("from")
        to_date = request.query_params.get("to")

        # Database aggregation groups by date and calculates averages
        qs = TelemetryRecord.objects.filter(device_id=device_id)
        if from_date: qs = qs.filter(created_at__date__gte=from_date)
        if to_date: qs = qs.filter(created_at__date__lte=to_date)

        stats = qs.annotate(date=TruncDate('created_at')).values('date').annotate(
            avg_hr=Avg('avg_heart_rate'), min_hr=Min('min_heart_rate'), max_hr=Max('max_heart_rate'),
            avg_o2=Avg('avg_spo2'), min_o2=Min('min_spo2'), max_o2=Max('max_spo2'),
            avg_temp=Avg('avg_object_temp'), max_temp=Max('max_object_temp'),
            avg_ax=Avg('accel_x'), avg_ay=Avg('accel_y'), avg_az=Avg('accel_z')
        ).order_by('date')

        response_data = {
            "from": from_date, "to": to_date,
            "data": {"heart": [], "spo2": [], "temperature": [], "accel": []}
        }

        for entry in stats:
            date_str = entry['date'].strftime('%Y-%m-%d')
            response_data["data"]["heart"].append({
                "avg_heart_rate": round(entry['avg_hr'], 1) if entry['avg_hr'] else None,
                "min_heart_rate": entry['min_hr'], "max_heart_rate": entry['max_hr'], "date": date_str
            })
            response_data["data"]["spo2"].append({
                "avg_spo2": round(entry['avg_o2'], 1) if entry['avg_o2'] else None,
                "min_spo2": entry['min_o2'], "max_spo2": entry['max_o2'], "date": date_str
            })
            response_data["data"]["temperature"].append({
                "avg_temp": round(entry['avg_temp'], 1) if entry['avg_temp'] else None,
                "max_temp": entry['max_temp'], "date": date_str
            })
            response_data["data"]["accel"].append({
                "x": round(entry['avg_ax'], 3), "y": round(entry['avg_ay'], 3), 
                "z": round(entry['avg_az'], 3), "date": date_str
            })

        return Response(response_data)

    @action(detail=False, methods=["get"], url_path=r"device/(?P<device_id>\d+)")
    def by_device(self, request, device_id=None):
        """Raw history filtered for a specific collar."""
        qs = TelemetryRecord.objects.filter(device_id=device_id).order_by("-created_at")
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
        
        return Response({"from": from_date, "to": to_date, "results": self.get_serializer(qs, many=True).data})