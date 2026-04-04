from rest_framework import viewsets, permissions
from .models import Pet
from .serializers import PetSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(tags=["Pets"], description="Retrieve all pets belonging to the authenticated user."),
    retrieve=extend_schema(tags=["Pets"], description="Retrieve details of a specific pet owned by the user."),
    create=extend_schema(tags=["Pets"], description="Create a new pet record and link it to your account."),
    update=extend_schema(tags=["Pets"], description="Update your pet's record."),
    destroy=extend_schema(tags=["Pets"], description="Remove a pet record from your account.")
)
class PetViewSet(viewsets.ModelViewSet):
    serializer_class = PetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        This is the most important part: 
        Only return pets that belong to the logged-in user.
        We use select_related to make it faster.
        """
        return Pet.objects.filter(owner=self.request.user).select_related('device', 'breed')

    def perform_create(self, serializer):
        """
        When the user clicks 'Save' in your React app, 
        this automatically attaches their User account to the Pet.
        """
        serializer.save(owner=self.request.user)