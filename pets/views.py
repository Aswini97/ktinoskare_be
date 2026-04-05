from rest_framework import viewsets, permissions
from .models import Pet
from .serializers import PetSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

@extend_schema_view(
    list=extend_schema(
        tags=["Pets"], 
        description="REQUIRED: ?owner_id=X to see your pets.",
        parameters=[OpenApiParameter("owner_id", type=int, required=True)]
    ),
    retrieve=extend_schema(
        tags=["Pets"], 
        description="REQUIRED: ?owner_id=X in URL to retrieve.",
        parameters=[OpenApiParameter("owner_id", type=int, required=True)]
    ),
    update=extend_schema(
        tags=["Pets"], 
        description="REQUIRED: ?owner_id=X in URL to update.",
        parameters=[OpenApiParameter("owner_id", type=int, required=True)]
    ),
    partial_update=extend_schema(
        tags=["Pets"], 
        description="REQUIRED: ?owner_id=X in URL to partially update.",
        parameters=[OpenApiParameter("owner_id", type=int, required=True)]
    ),
    destroy=extend_schema(
        tags=["Pets"], 
        description="REQUIRED: ?owner_id=X in URL to delete.",
        parameters=[OpenApiParameter("owner_id", type=int, required=True)]
    ),
    create=extend_schema(tags=["Pets"], description="Create a pet record manually.")
)
class PetViewSet(viewsets.ModelViewSet):
    serializer_class = PetSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """
        MANDATORY FILTER: Requires 'owner_id' query parameter for ALL actions.
        """
        owner_id = self.request.query_params.get('owner_id')
        
        if not owner_id:
            return Pet.objects.none()
            
        # Matches 'owner' field in your Pet model
        return Pet.objects.filter(owner=owner_id).select_related('device', 'breedId')

    def perform_create(self, serializer):
        """
        The owner ID must be provided in the JSON body since auth is disabled.
        """
        serializer.save()