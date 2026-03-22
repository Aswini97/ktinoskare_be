import os
import sys
import json
import paho.mqtt.client as mqtt
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ktinoskare.settings")
django.setup()

from telemetry.models import TelemetryRecord, Device

BROKER = "mqtt"
PORT = 1883
TOPIC = "v1/cattle/+/telemetry"

def on_connect(client, userdata, flags, rc):
    print(f"Connected to Broker with result code: {rc}")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"Received telemetry from {payload.get('device_uid')}")

        # Find the device
        device = Device.objects.get(device_uid=payload["device_uid"])

        TelemetryRecord.objects.create(
            device=device,
            heart_rate=payload.get("heart_rate"),
            spo2=payload.get("spo2"),
            ambient_temperature=payload.get("ambient_temperature"),
            object_temperature=payload.get("object_temperature"),
            accel_x=payload.get("accel_x"),
            accel_y=payload.get("accel_y"),
            accel_z=payload.get("accel_z"),
            motion_detected=payload.get("motion_detected", False),
            light_level=payload.get("light_level"),
            battery_voltage=payload.get("battery_voltage"),
            battery_percentage=payload.get("battery_percentage"),
            latitude=payload.get("latitude"),
            longitude=payload.get("longitude"),
        )
    except Exception as e:
        print(f"Error processing message: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_forever()