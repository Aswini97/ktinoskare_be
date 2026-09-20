from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import UserAccount
from .serializers import (
    UserAccountSerializer, 
    SignUpSerializer, 
    LoginSerializer, 
    UserSerializer,
    get_tokens_for_user
)

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
        return UserAccount.objects.filter(is_deleted=False).select_related('user').order_by('-created_at')

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            username = instance.user.username
            
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

    @extend_schema(
        tags=["Auth"],
        description="Register a new user and return JWT tokens with profile details.",
        request=SignUpSerializer,
        responses={201: UserAccountSerializer}
    )
    @action(detail=False, methods=['post'], url_path='signup')
    def signup(self, request):
        serializer = SignUpSerializer(data=request.data)
        if serializer.is_valid():
            account = serializer.save()
            tokens = get_tokens_for_user(account.user)

            return Response({
                "status": "success",
                "message": "User registered successfully.",
                "tokens": tokens,
                "user": UserSerializer(account.user).data,
                "account": UserAccountSerializer(account).data
            }, status=status.HTTP_201_CREATED)
            
        return Response({
            "status": "failure",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        tags=["Auth"],
        description="Authenticate user with username and password and issue JWT tokens.",
        request=LoginSerializer
    )
    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = get_tokens_for_user(user)

            account_data = None
            if hasattr(user, 'profile') and not user.profile.is_deleted:
                account_data = UserAccountSerializer(user.profile).data

            return Response({
                "status": "success",
                "message": "Login successful.",
                "tokens": tokens,
                "user": UserSerializer(user).data,
                "account": account_data
            }, status=status.HTTP_200_OK)

        return Response({
            "status": "failure",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)