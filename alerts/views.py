from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Alert
from .serializers import AlertSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(tags=["Alerts"], description="Retrieve all alerts for your pets."),
    retrieve=extend_schema(tags=["Alerts"], description="Retrieve details of a specific alert."),
    update=extend_schema(tags=["Alerts"], description="Update alert status."),
    destroy=extend_schema(tags=["Alerts"], description="Delete an alert record.")
)
class AlertViewSet(viewsets.ModelViewSet):
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Security: Only return alerts for devices linked to pets owned by the user.
        """
        return Alert.objects.filter(
            device__pet__owner=self.request.user
        ).select_related('device', 'device__pet').order_at("-created_at")

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """
        Custom endpoint to mark an alert as resolved.
        POST /api/alerts/{id}/resolve/
        """
        alert = self.get_object()
        alert.is_resolved = True
        alert.save()
        return Response({'status': 'alert resolved'}, status=status.HTTP_200_OK)