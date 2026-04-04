from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Alert
from .serializers import AlertSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

@extend_schema_view(
    list=extend_schema(
        tags=["Alerts"], 
        description="Retrieve alerts. Use ?user_id=X to filter.",
        parameters=[OpenApiParameter("user_id", type=int)]
    ),
    retrieve=extend_schema(tags=["Alerts"], description="Retrieve details of a specific alert."),
    update=extend_schema(tags=["Alerts"], description="Update alert status."),
    partial_update=extend_schema(tags=["Alerts"], description="Partially update an alert."),
    destroy=extend_schema(tags=["Alerts"], description="Delete an alert record.")
)
class AlertViewSet(viewsets.ModelViewSet):
    serializer_class = AlertSerializer
    permission_classes = [permissions.AllowAny] # No Auth

    def get_queryset(self):
        """
        Filters alerts by the pet owner's ID.
        """
        queryset = Alert.objects.all().select_related('device', 'device__pet')
        user_id = self.request.query_params.get('user_id')
        
        if user_id:
            return queryset.filter(device__pet__owner=user_id).order_by("-created_at")
        return queryset.order_by("-created_at")

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """
        Mark an alert as resolved. POST /api/alerts/{id}/resolve/
        """
        alert = self.get_object()
        alert.is_resolved = True
        alert.save()
        return Response({'status': 'alert resolved'}, status=status.HTTP_200_OK)