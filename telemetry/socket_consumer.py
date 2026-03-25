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

        # Handle initial request with device_uid
        if "device_uid" in data:
            device_uid = data["device_uid"]
            self.group_name = f"device_{device_uid}" # Match the name in mqtt_consumer.py

            # ✅ CRITICAL: Join the group so you can hear the MQTT broadcasts
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            
            print(f"📡 Socket joined group: {self.group_name}")
            
            try:
                from devices.models import Device
                self.device = await asyncio.to_thread(
                    Device.objects.get, device_uid=device_uid
                )
            except Exception:
                await self.send(json.dumps({"error": "Device not found"}))

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
                        payload = {
                            "id": latest.id,
                            "device_id": latest.device_id,
                            "created_at": str(latest.created_at),
                            "heart_rate": getattr(latest, "heart_rate", None),
                            "spo2": getattr(latest, "spo2", None),
                            "ambient_temperature": getattr(latest, "ambient_temperature", None),
                            "object_temperature": getattr(latest, "object_temperature", None),
                            "accel_x": getattr(latest, "accel_x", None),
                            "accel_y": getattr(latest, "accel_y", None),
                            "accel_z": getattr(latest, "accel_z", None),
                            "motion_detected": getattr(latest, "motion_detected", None),
                            "light_level": getattr(latest, "light_level", None),
                            "battery_voltage": getattr(latest, "battery_voltage", None),
                            "battery_percentage": getattr(latest, "battery_percentage", None),
                            "latitude": getattr(latest, "latitude", None),
                            "longitude": getattr(latest, "longitude", None),
                        }
                        await self.send(json.dumps({"telemetry": payload}))
                # Heartbeat
                await self.send(json.dumps({"heartbeat": True}))
                await asyncio.sleep(self.interval)
        except asyncio.CancelledError:
            pass

    # Handler for telemetry messages pushed into the group by mqtt_consumer
    async def telemetry_message(self, event):
        await self.send(json.dumps({"telemetry": event["data"]}))