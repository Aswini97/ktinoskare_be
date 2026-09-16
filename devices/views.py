import json
import paho.mqtt.client as mqtt
from django.conf import settings
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, inline_serializer
from rest_framework import serializers

from .models import Device
from .serializers import DeviceSerializer

# 1. Custom pagination class for Devices
class DevicePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            "count": self.page.paginator.count,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "results": data
        })

@extend_schema_view(
    list=extend_schema(
        tags=["Devices"], 
        description="List all trackers. Use ?user_id=X to filter. Supports ?page=X and ?page_size=X.",
        parameters=[
            OpenApiParameter("user_id", type=int, required=True),
            OpenApiParameter("page", type=int),
            OpenApiParameter("page_size", type=int)
        ]
    ),
    retrieve=extend_schema(tags=["Devices"], parameters=[OpenApiParameter("user_id", type=int, required=True)]),
    update=extend_schema(tags=["Devices"], parameters=[OpenApiParameter("user_id", type=int, required=True)]),
    partial_update=extend_schema(tags=["Devices"], parameters=[OpenApiParameter("user_id", type=int, required=True)]),
    destroy=extend_schema(tags=["Devices"], parameters=[OpenApiParameter("user_id", type=int, required=True)]),
    create=extend_schema(tags=["Devices"])
)
class DeviceViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = DevicePagination
    lookup_field = 'device_uid'  # Allows /api/v1/devices/<device_uid>/ rather than database ID

    def get_queryset(self):
        user_id = self.request.query_params.get('user_id')
        
        # When triggering detail actions (like OTA) where user_id param may not be passed
        if self.action in ['ota', 'retrieve', 'destroy', 'update', 'partial_update'] and not user_id:
            return Device.objects.all()

        if not user_id:
            return Device.objects.none()
            
        return Device.objects.filter(owner_id=user_id).order_by('id')

    def perform_create(self, serializer):
        serializer.save()
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        device_uid = instance.device_uid
        self.perform_destroy(instance)
        return Response({
            "status": "success",
            "message": f"Device {device_uid} has been deleted successfully."
        }, status=status.HTTP_200_OK)

    @extend_schema(
        tags=["Devices"],
        description="Trigger an Over-The-Air (OTA) firmware upgrade command to the collar via MQTT.",
        request=inline_serializer(
            name="TriggerOTARequest",
            fields={
                "version": serializers.CharField(default="1.0.1"),
                "url": serializers.URLField(default="http://13.233.104.107/firmware/firmware_v1.0.1.bin")
            }
        ),
        responses={200: inline_serializer(
            name="TriggerOTAResponse",
            fields={"message": serializers.CharField()}
        )}
    )
    @action(detail=True, methods=['post'], url_path='ota')
    def ota(self, request, device_uid=None):
        """
        POST /api/v1/devices/<device_uid>/ota/
        """
        device = self.get_object()
        target_version = request.data.get("version")
        firmware_url = request.data.get("url")

        if not target_version or not firmware_url:
            return Response(
                {"error": "Both 'version' and 'url' fields are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Match the JSON contract expected by the ESP32 firmware
        payload = json.dumps({
            "action": "ota_update",
            "version": target_version,
            "url": firmware_url
        })

        topic = f"ktinoscare/device/{device.device_uid}/cmd"

        try:
            client = mqtt.Client()
            # In Docker compose, 'emqx' is the broker service hostname
            broker_host = getattr(settings, "MQTT_BROKER_HOST", "emqx")
            client.connect(broker_host, 1883, 60)
            client.publish(topic, payload, qos=1)
            client.disconnect()

            return Response({
                "status": "success",
                "message": f"OTA update command published successfully to {topic}",
                "payload": json.loads(payload)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Failed to deliver command to broker: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )