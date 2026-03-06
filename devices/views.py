from rest_framework import viewsets
from devices.models import Device
from devices.serializers import DeviceSerializer

# Create your views here.
class DeviceListView(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer