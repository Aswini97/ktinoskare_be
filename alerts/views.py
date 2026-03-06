from django.shortcuts import render

from alerts.models import Device
from alerts.serializers import DeviceSerializer

# Create your views here.

class DeviceViewSet(viewsets.ModelViewSet):
    queryset = Device.objects.all()
    serializer_class = DeviceSerializer