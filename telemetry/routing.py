from django.urls import re_path
from . import socket_consumer

TelemetryConsumer = socket_consumer.TelemetryConsumer
websocket_urlpatterns = [
    re_path(r"^ws/telemetry/(?P<device_uid>\d+)/$", TelemetryConsumer.as_asgi()),
]