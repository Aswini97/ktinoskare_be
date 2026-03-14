from rest_framework.routers import DefaultRouter
from .views import DeviceListView

router = DefaultRouter()
router.register('', DeviceListView, basename='devices')

urlpatterns = router.urls