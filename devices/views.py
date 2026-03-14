from rest_framework import viewsets
from devices.models import Device
from devices.serializers import DeviceSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(tags=["Devices"], description="Retrieve a list of all devices in the system."),
    create=extend_schema(tags=["Devices"], description="Create a new device record."),
    retrieve=extend_schema(tags=["Devices"], description="Retrieve details of a specific device by its ID."),
    update=extend_schema(tags=["Devices"], description="Update an existing device record by its ID."),
    partial_update=extend_schema(tags=["Devices"], description="Partially update an existing device record by its ID."),
    destroy=extend_schema(tags=["Devices"], description="Delete a device record by its ID.")
)
class DeviceListView(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer