from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserAccount

def get_tokens_for_user(user):
    """
    Generate SimpleJWT refresh and access tokens for a given User instance.
    """
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'password']
        extra_kwargs = {
            'password': {'write_only': True, 'min_length': 6}
        }

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class UserAccountSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='user'
    )
    username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = UserAccount
        fields = ['id', 'user_id', 'username', 'phone', 'address', 'role', 'emergency_contact', 'is_deleted', 'created_at']

class SignUpSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, min_length=6)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    
    phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=UserAccount.ROLE_CHOICES, default='OWNER')
    emergency_contact = serializers.CharField(max_length=50, required=False, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value

    def create(self, validated_data):
        phone = validated_data.pop('phone', None)
        address = validated_data.pop('address', None)
        role = validated_data.pop('role', 'OWNER')
        emergency_contact = validated_data.pop('emergency_contact', None)

        with transaction.atomic():
            user = User.objects.create_user(**validated_data)
            account = UserAccount.objects.create(
                user=user,
                phone=phone,
                address=address,
                role=role,
                emergency_contact=emergency_contact
            )
        return account

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            raise serializers.ValidationError("Must include both 'username' and 'password'.")

        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")

        data['user'] = user
        return data