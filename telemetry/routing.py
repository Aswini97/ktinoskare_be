from django.urls import re_path
from . import socket_consumer

websocket_urlpatterns = [
    re_path(r"^ws/telemetry/(?P<device_uid>[\w_]+)/$", socket_consumer.TelemetryConsumer.as_asgi()),
]