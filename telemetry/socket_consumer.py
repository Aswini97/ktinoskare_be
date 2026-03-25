# telemetry/consumers.py
import json
import asyncio
from datetime import timedelta
from django.utils import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import TelemetryRecord, Device

class TelemetryConsumer(AsyncWebsocketConsumer):
    DEFAULT_INTERVAL = 30  # seconds

    async def connect(self):
        await self.accept()
        self.device = None
        self.interval = self.DEFAULT_INTERVAL
        self.task = None
        await self.send(json.dumps({"status": "connected", "heartbeat": True}))

    async def disconnect(self, close_code):
        if self.task:
            self.task.cancel()
        await self.send(json.dumps({"status": "terminated"}))

    async def receive(self, text_data):
        data = json.loads(text_data)

        # Handle initial request with collar_id
        if "collar_id" in data:
            try:
                self.device = await asyncio.to_thread(
                    Device.objects.get, device_uid=data["collar_id"]
                )
            except Device.DoesNotExist:
                await self.send(json.dumps({"error": "Device not found"}))
                return

            # # Send last 7 days of telemetry
            # since = timezone.now() - timedelta(days=7)
            # records = await asyncio.to_thread(
            #     lambda: list(
            #         TelemetryRecord.objects.filter(
            #             device=self.device, created_at__gte=since
            #         ).order_by("created_at").values()
            #     )
            # )
            # await self.send(json.dumps({"last_7_days": records}))

        # Handle interval update
        if "interval" in data:
            try:
                self.interval = int(data["interval"])
            except ValueError:
                self.interval = self.DEFAULT_INTERVAL

            if self.task:
                self.task.cancel()
            self.task = asyncio.create_task(self.stream_data())

        # Handle terminate request
        if data.get("terminate"):
            if self.task:
                self.task.cancel()
            await self.send(json.dumps({"status": "terminated"}))
            await self.close()

    async def stream_data(self):
        try:
            while True:
                if self.device:
                    latest = await asyncio.to_thread(
                        lambda: TelemetryRecord.objects.filter(
                            device=self.device
                        ).order_by("-created_at").first()
                    )
                    if latest:
                        await self.send(json.dumps({"telemetry": latest.__dict__}))
                # Heartbeat
                await self.send(json.dumps({"heartbeat": True}))
                await asyncio.sleep(self.interval)
        except asyncio.CancelledError:
            pass