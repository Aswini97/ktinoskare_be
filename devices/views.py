import json
import paho.mqtt.publish as publish
from django.conf import settings
from django.db import transaction
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, inline_serializer
from rest_framework import serializers

from .models import *
from .serializers import *


class StandardPagination(PageNumberPagination):
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
        tags=["Device Master"],
        description="List all manufactured hardware units in master catalog. Supports pagination (?page=X&page_size=X).",
        parameters=[
            OpenApiParameter("page", type=int, required=False),
            OpenApiParameter("page_size", type=int, required=False)
        ]
    ),
    retrieve=extend_schema(tags=["Device Master"]),
    update=extend_schema(tags=["Device Master"]),
    partial_update=extend_schema(tags=["Device Master"]),
    destroy=extend_schema(tags=["Device Master"]),
    create=extend_schema(tags=["Device Master"])
)
class DeviceMasterViewSet(viewsets.ModelViewSet):
    queryset = DeviceMaster.objects.all().order_by('-created_at')
    serializer_class = DeviceMasterSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardPagination
    lookup_field = 'device_uid'

    @extend_schema(
        tags=["Device Master"],
        description="Factory bulk intake: Register one or multiple standalone hardware units into the master catalog.",
        request=DeviceMasterSerializer(many=True),
        responses={201: DeviceMasterSerializer(many=True)}
    )
    @action(detail=False, methods=['post'], url_path='bulk-register')
    def bulk_register(self, request):
        payload = request.data
        data = payload if isinstance(payload, list) else [payload]

        if not data:
            return Response(
                {"status": "failure", "message": "Payload cannot be empty."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = DeviceMasterSerializer(data=data, many=True)
        if not serializer.is_valid():
            return Response(
                {"status": "failure", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        master_instances = [DeviceMaster(**item) for item in serializer.validated_data]

        with transaction.atomic():
            created_units = DeviceMaster.objects.bulk_create(master_instances)

        return Response(
            {
                "status": "success",
                "count": len(created_units),
                "devices": DeviceMasterSerializer(created_units, many=True).data
            },
            status=status.HTTP_201_CREATED
        )


@extend_schema_view(
    list=extend_schema(
        tags=["User Devices"],
        description="List registered customer collars. Optionally filter by ?user_id=X. Supports pagination.",
        parameters=[
            OpenApiParameter("user_id", type=int, required=False),
            OpenApiParameter("page", type=int, required=False),
            OpenApiParameter("page_size", type=int, required=False)
        ]
    ),
    retrieve=extend_schema(tags=["User Devices"]),
    update=extend_schema(tags=["User Devices"]),
    partial_update=extend_schema(tags=["User Devices"]),
    destroy=extend_schema(tags=["User Devices"]),
    create=extend_schema(tags=["User Devices"])
)
class UserDeviceMappingViewSet(viewsets.ModelViewSet):
    serializer_class = UserDeviceMappingSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardPagination
    lookup_field = 'device__device_uid'

    def get_queryset(self):
        queryset = UserDeviceMapping.objects.select_related('device', 'user').order_by('-assigned_at')
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        return queryset

    def create(self, request, *args, **kwargs):
        device_uid = request.data.get('device_uid')
        user_id = request.data.get('user')

        if not device_uid or not user_id:
            return Response(
                {"status": "failure", "message": "Both 'device_uid' and 'user' fields are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not DeviceMaster.objects.filter(device_uid=device_uid).exists():
            return Response(
                {"status": "failure", "message": f"Hardware unit '{device_uid}' is not registered in DeviceMaster."},
                status=status.HTTP_404_NOT_FOUND
            )

        if UserDeviceMapping.objects.filter(device__device_uid=device_uid).exists():
            return Response(
                {"status": "failure", "message": f"Hardware unit '{device_uid}' is already mapped to an account."},
                status=status.HTTP_409_CONFLICT
            )

        return super().create(request, *args, **kwargs)

    @extend_schema(
        tags=["User Devices"],
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
    def ota(self, request, device__device_uid=None):
        mapping = self.get_object()
        target_version = request.data.get("version")
        firmware_url = request.data.get("url")

        if not target_version or not firmware_url:
            return Response(
                {"error": "Both 'version' and 'url' fields are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        payload = json.dumps({
            "action": "ota_update",
            "version": target_version,
            "url": firmware_url
        })

        topic = f"ktinoscare/device/{mapping.device.device_uid}/cmd"
        broker_host = getattr(settings, "MQTT_BROKER_HOST", "mqtt")
        broker_port = int(getattr(settings, "MQTT_BROKER_PORT", 1883))

        try:
            publish.single(
                topic=topic,
                payload=payload,
                hostname=broker_host,
                port=broker_port,
                qos=1,
                retain=False
            )
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

    @extend_schema(
        tags=["User Devices"],
        description="Dynamically adjust telemetry transmission interval on collar via MQTT.",
        request=inline_serializer(
            name="SetIntervalRequest",
            fields={"interval_seconds": serializers.IntegerField(default=30)}
        ),
        responses={200: inline_serializer(
            name="SetIntervalResponse",
            fields={"message": serializers.CharField()}
        )}
    )
    @action(detail=True, methods=['post'], url_path='interval')
    def set_interval(self, request, device__device_uid=None):
        mapping = self.get_object()
        raw_interval = request.data.get('interval_seconds')

        if raw_interval is None:
            return Response(
                {"status": "failure", "message": "Field 'interval_seconds' is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            interval_seconds = int(raw_interval)
            if not (3 <= interval_seconds <= 3600):
                raise ValueError
        except (ValueError, TypeError):
            return Response(
                {
                    "status": "failure",
                    "message": "interval_seconds must be an integer between 3 and 3600 (1 hour)."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        cmd_payload = {
            "action": "set_interval",
            "interval_seconds": interval_seconds
        }
        topic = f"ktinoscare/device/{mapping.device.device_uid}/cmd"

        broker_host = getattr(settings, 'MQTT_BROKER_HOST', 'mqtt')
        broker_port = int(getattr(settings, 'MQTT_BROKER_PORT', 1883))

        try:
            publish.single(
                topic=topic,
                payload=json.dumps(cmd_payload),
                hostname=broker_host,
                port=broker_port,
                qos=1,
                retain=False
            )
        except Exception as e:
            return Response(
                {"status": "failure", "message": f"Failed to publish MQTT command: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {
                "status": "success",
                "message": f"Interval set to {interval_seconds}s for device {mapping.device.device_uid}",
                "payload": cmd_payload
            },
            status=status.HTTP_200_OK
        )