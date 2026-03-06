from rest_framework.routers import DefaultRouter
from .views import TelemetryRecordViewSet

router = DefaultRouter()
router.register('', TelemetryRecordViewSet, basename='telemetry')

urlpatterns = router.urls