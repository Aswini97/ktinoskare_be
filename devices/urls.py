from rest_framework.routers import DefaultRouter
from .views import DeviceListView

router = DefaultRouter()
router.register('devices', DeviceListView, basename='devices')

urlpatterns = router.urls