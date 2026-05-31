from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

urlpatterns = [

    # Admin
    path('admin/', admin.site.urls),

    # API v1
    path('api/v1/accounts/', include('accounts.urls')),
    path('api/v1/devices/', include('devices.urls')),
    path('api/v1/pets/', include('pets.urls')),
    path('api/v1/telemetry/', include('telemetry.urls')),
    path('api/v1/alerts/', include('alerts.urls')),

    # OpenAPI schema
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),

    # Redoc documentation
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc',
    ),
]