from rest_framework import viewsets, permissions
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


@extend_schema_view(
    list=extend_schema(tags=["Pet Categories"], description="List all pet categories (e.g., Cattle, Dogs)."),
    create=extend_schema(tags=["Pet Categories"]),
    retrieve=extend_schema(tags=["Pet Categories"]),
    update=extend_schema(tags=["Pet Categories"]),
    partial_update=extend_schema(tags=["Pet Categories"]),
    destroy=extend_schema(tags=["Pet Categories"]),
)
class PetCategoryViewSet(viewsets.ModelViewSet):
    """
    CRUD for Pet Categories.
    """
    queryset = PetCategory.objects.all().order_by('name')
    serializer_class = PetCategorySerializer
    permission_classes = [permissions.AllowAny]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        self.perform_destroy(instance)
        return Response({
            "status": "success",
            "message": f"Category '{name}' deleted successfully."
        }, status=status.HTTP_200_OK)


@extend_schema_view(
    list=extend_schema(
        tags=["Pet Breeds"], 
        description="List breeds. Optional: ?category_id=X to filter by category.",
        parameters=[OpenApiParameter("category_id", type=int, required=False)]
    ),
    create=extend_schema(tags=["Pet Breeds"]),
    retrieve=extend_schema(tags=["Pet Breeds"]),
    update=extend_schema(tags=["Pet Breeds"]),
    partial_update=extend_schema(tags=["Pet Breeds"]),
    destroy=extend_schema(tags=["Pet Breeds"]),
)
class PetBreadViewSet(viewsets.ModelViewSet):
    """
    CRUD for Pet Breeds (naming follows your PetBread model).
    """
    serializer_class = PetBreadSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = PetBread.objects.all().select_related('category').order_by('name')
        category_id = self.request.query_params.get('category_id')
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        name = instance.name
        self.perform_destroy(instance)
        return Response({
            "status": "success",
            "message": f"Breed '{name}' deleted successfully."
        }, status=status.HTTP_200_OK)