from rest_framework import viewsets
from .models import Alert
from .serializers import AlertSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(tags=["Alerts"], description="Retrieve a list of all alerts in the system."),
    retrieve=extend_schema(tags=["Alerts"], description="Retrieve details of a specific alert by its ID."),
    create=extend_schema(tags=["Alerts"], description="Create a new alert in the system."),
    update=extend_schema(tags=["Alerts"], description="Update an existing alert by its ID."),
    partial_update=extend_schema(tags=["Alerts"], description="Partially update an existing alert by its ID."),
    destroy=extend_schema(tags=["Alerts"], description="Delete an alert by its ID.")
)
class AlertViewSet(viewsets.ModelViewSet):
    queryset = Alert.objects.all()
    serializer_class = AlertSerializer