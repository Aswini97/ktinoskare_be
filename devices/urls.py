from rest_framework.routers import DefaultRouter
from .views import DeviceMasterViewSet, UserDeviceMappingViewSet

router = DefaultRouter()
router.register('master', DeviceMasterViewSet, basename='device-master')
router.register('user', UserDeviceMappingViewSet, basename='user-device-mappings')

urlpatterns = router.urls