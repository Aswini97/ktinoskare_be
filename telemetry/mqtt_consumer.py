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
        data = msg.payload.decode().split(",")
        print(f"Received telemetry from {data[0]}")

        device = Device.objects.get(device_uid=data[0])

        TelemetryRecord.objects.create(
            device=device,
            heart_rate=float(data[1]),
            spo2=float(data[2]),
            ambient_temperature=float(data[3]),
            object_temperature=float(data[4]),
            accel_x=float(data[5]),
            accel_y=float(data[6]),
            accel_z=float(data[7]),
            motion_detected=(data[8] == "1"),
            light_level=float(data[9]),
            battery_voltage=float(data[10]),
            battery_percentage=int(data[11]),
            latitude=float(data[12]),
            longitude=float(data[13]),
        )
    except Exception as e:
        print(f"Error processing message: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_forever()