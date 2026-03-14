from rest_framework import viewsets
from .models import UserAccount
from .serializers import UserAccountSerializer
from drf_spectacular.utils import extend_schema, extend_schema_view

@extend_schema_view(
    list=extend_schema(tags=["Accounts"], description="Retrieve a list of all user accounts in the system."),
    retrieve=extend_schema(tags=["Accounts"], description="Retrieve details of a specific user account by its ID."),
    create=extend_schema(tags=["Accounts"], description="Create a new user account."),
    update=extend_schema(tags=["Accounts"], description="Update an existing user account."),
    partial_update=extend_schema(tags=["Accounts"], description="Partially update an existing user account."),
    destroy=extend_schema(tags=["Accounts"], description="Delete a user account.")
)
class AccountViewSet(viewsets.ModelViewSet):
    queryset = UserAccount.objects.all()
    serializer_class = UserAccountSerializer
