from rest_framework import viewsets, permissions
from .models import Pet
from .serializers import PetSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

@extend_schema_view(
    list=extend_schema(
        tags=["Pets"], 
        description="Retrieve pets. Use ?owner_id=X to filter.",
        parameters=[OpenApiParameter("owner_id", type=int)]
    ),
    retrieve=extend_schema(tags=["Pets"], description="Retrieve details of a specific pet."),
    create=extend_schema(tags=["Pets"], description="Create a new pet. You must pass 'owner' ID in the body."),
    update=extend_schema(tags=["Pets"], description="Update a pet record."),
    destroy=extend_schema(tags=["Pets"], description="Remove a pet record.")
)
class PetViewSet(viewsets.ModelViewSet):
    serializer_class = PetSerializer
    permission_classes = [permissions.AllowAny] # No Auth

    def get_queryset(self):
        """
        Filters the list of pets based on the 'owner_id' query parameter.
        """
        queryset = Pet.objects.all().select_related('device', 'breedId') # Matches your model
        owner_id = self.request.query_params.get('owner_id')
        
        if owner_id:
            return queryset.filter(owner=owner_id) # Matches 'owner' field
        return queryset