from rest_framework import viewsets
from .models import Pet
from .serializers import PetSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(tags=["Pets"], description="Retrieve a list of all pets in the system."),
    retrieve=extend_schema(tags=["Pets"], description="Retrieve details of a specific pet by its ID."),
    create=extend_schema(tags=["Pets"], description="Create a new pet record in the system."),
    update=extend_schema(tags=["Pets"], description="Update an existing pet record by its ID."),
    partial_update=extend_schema(tags=["Pets"], description="Partially update an existing pet record by its ID."),
    destroy=extend_schema(tags=["Pets"], description="Delete a pet record by its ID.")
)
class PetViewSet(viewsets.ModelViewSet):
    queryset = Pet.objects.all()
    serializer_class = PetSerializer
