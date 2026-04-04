from rest_framework import viewsets, permissions
from .models import Device
from .serializers import DeviceSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

@extend_schema_view(
    list=extend_schema(
        tags=["Devices"], 
        description="List trackers. Use ?user_id=X to filter by owner.",
        parameters=[OpenApiParameter("user_id", type=int)]
    ),
    retrieve=extend_schema(tags=["Devices"], description="Get details of a specific tracker."),
    update=extend_schema(tags=["Devices"], description="Full update of a device record."),
    partial_update=extend_schema(tags=["Devices"], description="Partial update of a device record."),
    create=extend_schema(tags=["Devices"], exclude=True), 
    destroy=extend_schema(tags=["Devices"], exclude=True),
)
class DeviceViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceSerializer
    permission_classes = [permissions.AllowAny] # No Auth

    def get_queryset(self):
        """
        Filters devices by the pet's owner ID passed in the URL.
        """
        queryset = Device.objects.all().select_related('pet')
        user_id = self.request.query_params.get('user_id')
        
        if user_id:
            # Field lookup must be 'pet__owner'
            return queryset.filter(pet__owner=user_id)
        return queryset