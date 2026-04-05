from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PetViewSet, PetCategoryViewSet, PetBreadViewSet

router = DefaultRouter()

# Master Data endpoints (order matters for the router)
router.register('categories', PetCategoryViewSet, basename='pet-categories')
router.register('breeds', PetBreadViewSet, basename='pet-breeds')

# Main Pet Records
router.register('', PetViewSet, basename='pets')

urlpatterns = [
    path('', include(router.urls)),
]