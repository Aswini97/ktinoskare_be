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
        # 1. Print EXACTLY what is coming from the MQTT Broker
        raw_payload = msg.payload.decode().strip()
        print(f"\n--- INCOMING TELEMETRY ---")
        print(f"RAW: {raw_payload}")

        # 2. Split the CSV string
        data = raw_payload.split(",")
        
        # Guard against short messages or empty data
        if len(data) < 14:
            print(f"⚠️ Warning: Incomplete data packet (Length: {len(data)})")
            return

        device_uid = data[0].strip()
        
        # 3. Convert GPS fields specifically
        # .strip() is crucial to remove any hidden \r or \n from the end of the string
        lat_raw = data[12].strip()
        lon_raw = data[13].strip()
        
        lat = float(lat_raw)
        lon = float(lon_raw)

        print(f"DEBUG -> Lat: {lat} | Lon: {lon}")

        # 4. Filter out zeros (Don't save if GPS hasn't fixed yet)
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

    except Exception as e:
        print(f"🔥 Error processing message: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)
client.loop_forever()