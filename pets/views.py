from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Pet
from .serializers import *
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
        owner_id = self.request.query_params.get('owner_id')
        
        if not owner_id:
            return Pet.objects.none()

        return Pet.objects.filter(owner=owner_id).select_related('device', 'breed_id', 'species_id')

    def perform_create(self, serializer):
        serializer.save()


@extend_schema_view(
    list=extend_schema(tags=["Pet Species"], description="List all pet species (e.g., Cattle, Dogs)."),
    create=extend_schema(tags=["Pet Species"]),
    retrieve=extend_schema(tags=["Pet Species"]),
    update=extend_schema(tags=["Pet Species"]),
    partial_update=extend_schema(tags=["Pet Species"]),
    destroy=extend_schema(tags=["Pet Species"]),
)
class SpeciesViewSet(viewsets.ModelViewSet):
    queryset = Species.objects.all().order_by('name')
    serializer_class = SpeciesSerializer
    permission_classes = [permissions.AllowAny]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        self.perform_destroy(instance)
        return Response({
            "status": "success",
            "message": f"Species '{name}' deleted successfully."
        }, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        tags=["Pet Breeds"], 
        description="List breeds. Optional: ?species_id=X to filter by species.",
        parameters=[OpenApiParameter("species_id", type=int, required=False)]
    ),
    create=extend_schema(tags=["Pet Breeds"]),
    retrieve=extend_schema(tags=["Pet Breeds"]),
    update=extend_schema(tags=["Pet Breeds"]),
    partial_update=extend_schema(tags=["Pet Breeds"]),
    destroy=extend_schema(tags=["Pet Breeds"]),
)
class PetBreadViewSet(viewsets.ModelViewSet):
    serializer_class = PetBreadSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = PetBread.objects.all().select_related('species').order_by('name')
        species_id = self.request.query_params.get('species_id')
        
        if species_id:
            queryset = queryset.filter(species_id=species_id)
        return queryset

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        self.perform_destroy(instance)
        return Response({
            "status": "success",
            "message": f"Breed '{name}' deleted successfully."
        }, status=status.HTTP_200_OK)