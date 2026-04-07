from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserAccount

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class UserAccountSerializer(serializers.ModelSerializer):
    user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), 
        source='user'
    )
    username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = UserAccount
        fields = ['id', 'user_id', 'username', 'phone', 'address', 'is_deleted', 'created_at']