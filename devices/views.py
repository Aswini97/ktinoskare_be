from rest_framework import viewsets, permissions, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from .models import Device
from .serializers import DeviceSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

# 1. Define a custom pagination class for Devices
class DevicePagination(PageNumberPagination):
    page_size = 10  # Default page size if none provided
    page_size_query_param = 'page_size'  # Enables ?page_size=X
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data
        })

@extend_schema_view(
    list=extend_schema(
        tags=["Devices"], 
        description="List all trackers. Use ?user_id=X to filter. Supports ?page=X and ?page_size=X.",
        parameters=[
            OpenApiParameter("user_id", type=int, required=True),
            OpenApiParameter("page", type=int),
            OpenApiParameter("page_size", type=int)
        ]
    ),
    retrieve=extend_schema(tags=["Devices"], parameters=[OpenApiParameter("user_id", type=int, required=True)]),
    update=extend_schema(tags=["Devices"], parameters=[OpenApiParameter("user_id", type=int, required=True)]),
    partial_update=extend_schema(tags=["Devices"], parameters=[OpenApiParameter("user_id", type=int, required=True)]),
    destroy=extend_schema(tags=["Devices"], parameters=[OpenApiParameter("user_id", type=int, required=True)]),
    create=extend_schema(tags=["Devices"])
)
class DeviceViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceSerializer
    permission_classes = [permissions.AllowAny]
    # 2. Add the pagination class here
    pagination_class = DevicePagination

    def get_queryset(self):
        """
        Filters by owner_id using the mandatory user_id query parameter.
        """
        user_id = self.request.query_params.get('user_id')
        
        if not user_id:
            return Device.objects.none()
            
        # Matches the 'owner_id' column in your database
        return Device.objects.filter(owner_id=user_id).order_by('id')

    def perform_create(self, serializer):
        serializer.save()
    
    def destroy(self, request, *args, **kwargs):
        """
        Overridden to return a custom success response (200 OK) instead of 204 No Content.
        """
        instance = self.get_object()
        device_uid = instance.device_uid
        self.perform_destroy(instance)
        return Response({
            "status": "success",
            "message": f"Device {device_uid} has been deleted successfully."
        }, status=status.HTTP_200_OK)