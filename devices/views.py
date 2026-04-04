from rest_framework import viewsets, permissions
from .models import Device
from .serializers import DeviceSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(tags=["Devices"], description="List all trackers currently linked to your pets."),
    retrieve=extend_schema(tags=["Devices"], description="Get details of a specific tracker you own."),
    update=extend_schema(tags=["Devices"], description="Full update of a device record."),
    partial_update=extend_schema(tags=["Devices"], description="Partial update (e.g., change name or firmware version) of a device."),
    # Keep these hidden if they are handled by Admin/System only
    create=extend_schema(tags=["Devices"], exclude=True), 
    destroy=extend_schema(tags=["Devices"], exclude=True),
)
class DeviceViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Ensures users can only view or UPDATE devices linked to their own pets.
        """
        return Device.objects.filter(pet__owner=self.request.user).select_related('pet')