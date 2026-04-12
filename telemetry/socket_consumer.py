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
        await self.send(json.dumps({"ok": True}))

    async def disconnect(self, close_code):
        if self.task:
            self.task.cancel()
        print("❌ WebSocket client disconnected")
        await self.send(json.dumps({"status": "terminated"}))

    async def receive(self, text_data):
        data = json.loads(text_data)

        # Handle initial request with duid
        if "duid" in data:
            device_uid = data["duid"]
            self.group_name = f"device_{device_uid}" # Match the name in mqtt_consumer.py

            # ✅ CRITICAL: Join the group so you can hear the MQTT broadcasts
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            
            print(f"📡 Socket joined group: {self.group_name}")
            
            # Send confirmation back to client
            await self.send(json.dumps({"ok": True}))
            
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
                        # Corrected mapping to match your models.py
                        payload = {
                            "id": latest.id,
                            "duid": self.device.device_uid,
                            "ts": latest.created_at.isoformat(),
                            "hr": latest.avg_heart_rate,
                            "spo2": latest.avg_spo2,
                            "amb_t": latest.avg_ambient_temp,
                            "obj_t": latest.avg_object_temp,
                            "ax": latest.accel_x,
                            "ay": latest.accel_y,
                            "az": latest.accel_z,
                            "motion": latest.motion_detected,
                            "light": latest.light_level,
                            "batt_v": latest.battery_voltage,
                            "batt_p": latest.battery_percentage,
                            "lat": latest.latitude,
                            "lon": latest.longitude,
                            "dht_t": latest.temp_dht22,
                            "hum": latest.humidity,
                            "hi": latest.heat_index,
                        }
                        await self.send(json.dumps({"telemetry": payload}))
                
                await asyncio.sleep(self.interval)
        except asyncio.CancelledError:
            pass

    # This handles the REAL-TIME push from your mqtt_worker
    async def telemetry_message(self, event):
        # We wrap it in a 'telemetry' key so the frontend 
        # only has to listen for one type of message
        await self.send(json.dumps({"telemetry": event["data"]}))