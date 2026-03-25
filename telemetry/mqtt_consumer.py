import os
import sys
import json
import paho.mqtt.client as mqtt
import django
from datetime import datetime
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Django setup
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
        # 1. Capture and Print EXACTLY when the data hits the script
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        raw_payload = msg.payload.decode().strip()
        
        print(f"\n--- INCOMING TELEMETRY [{now}] ---")
        print(f"RAW: {raw_payload}")

        # 2. Split the CSV string
        data = raw_payload.split(",")
        
        if len(data) < 14:
            print(f"⚠️ Warning: Incomplete data packet (Length: {len(data)})")
            return

        device_uid = data[0].strip()
        
        # 3. Convert GPS fields specifically
        lat_raw = data[12].strip()
        lon_raw = data[13].strip()
        
        lat = float(lat_raw)
        lon = float(lon_raw)

        print(f"DEBUG -> Lat: {lat} | Lon: {lon}")

        # 4. Filter out zeros
        if lat == 0.0 or lon == 0.0:
            print("❌ Skipping DB Save: GPS fix not yet acquired.")
            return

        # 5. Save to Django Database
        device = Device.objects.get(device_uid=device_uid)

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
            latitude=lat,
            longitude=lon,
        )
        print(f"✅ SUCCESS: Record saved for {device_uid}")

        # 6. Broadcast telemetry to WebSocket group
        try:
            channel_layer = get_channel_layer()
            print(f"📡 Channel Layer: {channel_layer}")
            group_name = f"device_{device_uid}"
            print(f"📡 Broadcasting to group: {group_name}")
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "telemetry_message",
                    "data": {
                        "duid": device_uid,
                        "lat": lat,
                        "long": lon,
                        "hr": float(data[1]),
                        "spo2": float(data[2]),
                        "amb_temp": float(data[3]),
                        "obj_temp": float(data[4]),
                        "ax": float(data[5]),
                        "ay": float(data[6]),
                        "az": float(data[7]),
                        "motion": (data[8] == "1"),
                        "light": float(data[9]),
                        "batt_v": float(data[10]),
                        "batt_pct": int(data[11]),
                    },
                }
            )
            print(f"📡 Broadcast sent successfully to {group_name}")
        except Exception as broadcast_error:
            print(f"🔥 Broadcast Error: {broadcast_error}")

    except Exception as e:
        print(f"🔥 Error processing message: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print(f"Subscriber started. Listening on {BROKER}...")
client.connect(BROKER, PORT, 60)
client.loop_forever()