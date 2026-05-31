import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils.timezone import now
from asgiref.sync import sync_to_async

class TelemetryConsumer(AsyncWebsocketConsumer):
    DEFAULT_INTERVAL = 10  # Reduced to keep client screens responsive

    async def connect(self):
        self.device_uid = self.scope['url_route']['kwargs'].get('device_uid')
        self.group_name = f"device_{self.device_uid}"
        self.keep_running = True

        # Join the multi-tenant real-time channel group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        print(f"✅ WebSocket client initialized channel bridge for device: {self.device_uid}")
        
        # Start the historical fallback logging stream thread asynchronously
        self.loop_task = asyncio.create_task(self.stream_historical_fallback())

    async def disconnect(self, close_code):
        self.keep_running = False
        if hasattr(self, 'loop_task'):
            self.loop_task.cancel()
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        print(f"❌ WebSocket client severed connection for device: {self.device_uid}")

    async def receive(self, text_data):
        """Processes dynamic incoming commands sent down from user interactive maps."""
        try:
            data = json.loads(text_data)
            print(f"🕹️ Command intercept from map console: {data}")
        except Exception as e:
            print(f"⚠️ Failed to parse incoming socket frame: {str(e)}")

    async def stream_historical_fallback(self):
        """Periodically streams the absolute latest data point if MQTT stream pauses."""
        from telemetry.models import TelemetryRecord
        
        try:
            while self.keep_running:
                # Resolve the lazy query safely inside an async context thread wrapper
                latest = await sync_to_async(
                    lambda: TelemetryRecord.objects.filter(device__device_uid=self.device_uid).order_by('-created_at').first()
                )()

                if latest and latest.location:
                    payload = {
                        "device_uid": self.device_uid,
                        "timestamp": latest.created_at.isoformat(),
                        "avg_heart_rate": latest.avg_heart_rate,
                        "avg_spo2": latest.avg_spo2,
                        "avg_object_temp": latest.avg_object_temp,
                        "motion_detected": latest.motion_detected,
                        # FIXED: Decodes native geometric primitives cleanly without attribute crashes
                        "latitude": latest.location.y, 
                        "longitude": latest.location.x,
                        "battery_percentage": latest.battery_percentage,
                        "humidity": latest.humidity,
                        "is_emergency": latest.is_emergency
                    }
                    await self.send(json.dumps({"telemetry": payload}))
                
                await asyncio.sleep(self.DEFAULT_INTERVAL)
        except asyncio.CancelledError:
            pass

    async def telemetry_message(self, event):
        """Intercepts immediate real-time multicast frames broadcast by mqtt_worker."""
        await self.send(json.dumps({"telemetry": event["data"]}))