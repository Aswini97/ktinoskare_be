from rest_framework import serializers
from .models import *

class PetSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    device_uid = serializers.ReadOnlyField(source='device.device_uid')

    class Meta:
        model = Pet
        fields = '__all__'

class PetCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PetCategory
        fields = '__all__'

class PetBreadSerializer(serializers.ModelSerializer):
    # Added to show the category name in the response for better UI display
    category_name = serializers.ReadOnlyField(source='category.name')

    class Meta:
        model = PetBread
        fields = ['id', 'name', 'category', 'category_name']