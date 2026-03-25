# telemetry/consumers.py
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer

class TelemetryConsumer(AsyncWebsocketConsumer):
    DEFAULT_INTERVAL = 30  # seconds

    async def connect(self):
        await self.accept()
        self.device = None
        self.interval = self.DEFAULT_INTERVAL
        self.task = None
        print("✅ WebSocket client connected")
        await self.send(json.dumps({"status": "connected", "heartbeat": True}))

    async def disconnect(self, close_code):
        if self.task:
            self.task.cancel()
        print("❌ WebSocket client disconnected")
        await self.send(json.dumps({"status": "terminated"}))

    async def receive(self, text_data):
        data = json.loads(text_data)

        # Handle initial request with collar_id
        if "collar_id" in data:
            try:
                # Import models only when needed
                from devices.models import Device
                self.device = await asyncio.to_thread(
                    Device.objects.get, device_uid=data["collar_id"]
                )
                print(f"📡 Device {self.device.device_uid} attached to socket")
            except Exception:
                await self.send(json.dumps({"error": "Device not found"}))
                return

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
                    from telemetry.models import TelemetryRecord
                    latest = await asyncio.to_thread(
                        lambda: TelemetryRecord.objects.filter(
                            device=self.device
                        ).order_by("-created_at").first()
                    )
                    if latest:
                        # Avoid sending raw __dict__ (contains internal fields)
                        payload = {
                            "id": latest.id,
                            "device_id": latest.device_id,
                            "created_at": str(latest.created_at),
                            "data": getattr(latest, "data", None),
                        }
                        await self.send(json.dumps({"telemetry": payload}))
                # Heartbeat
                await self.send(json.dumps({"heartbeat": True}))
                await asyncio.sleep(self.interval)
        except asyncio.CancelledError:
            pass