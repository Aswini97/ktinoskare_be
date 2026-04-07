from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import UserAccount
from .serializers import UserAccountSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(tags=["Accounts"], description="Retrieve a list of all active user profiles."),
    retrieve=extend_schema(tags=["Accounts"], description="Retrieve details of a specific active profile by its ID."),
    create=extend_schema(tags=["Accounts"], description="Create a new user profile."),
    update=extend_schema(tags=["Accounts"], description="Update an existing active user profile (Full Update)."),
    partial_update=extend_schema(tags=["Accounts"], description="Partially update an existing active user profile."),
    destroy=extend_schema(tags=["Accounts"], description="Soft-delete a user profile.")
)
class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = UserAccountSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        """
        Applies to list, retrieve, update, and partial_update.
        Ensures only non-deleted records are accessible.
        """
        return UserAccount.objects.filter(is_deleted=False).select_related('user').order_by('-created_at')

    def destroy(self, request, *args, **kwargs):
        """
        Performs a soft delete and returns a custom success/failure message.
        """
        try:
            # get_object() automatically respects the is_deleted=False filter in get_queryset
            instance = self.get_object()
            username = instance.user.username
            
            # Soft Delete Logic
            instance.is_deleted = True
            instance.deleted_at = timezone.now()
            instance.save()
            
            return Response({
                "status": "success",
                "message": f"Account profile for user '{username}' soft-deleted successfully."
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                "status": "failure",
                "message": f"Failed to delete account: {str(e)}"
            }, status=status.HTTP_400_BAD_REQUEST)