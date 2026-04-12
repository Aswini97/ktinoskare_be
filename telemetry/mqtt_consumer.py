import os
import sys
import django
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import paho.mqtt.client as mqtt

# Django setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ktinoskare.settings")
django.setup()

from telemetry.models import TelemetryRecord, Device

# --- CONFIGURATION ---
BROKER = "mqtt"
PORT = 1883
# Listen to both pet and cattle topics using a wildcard
TOPIC = "v1/+/+/telemetry" 

def on_connect(client, userdata, flags, rc):
    print(f"✅ Connected to Broker [Code {rc}]")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        # 1. Decode & Print Raw Data with Timestamp
        now = timezone.now()
        raw_payload = msg.payload.decode().strip()
        print(f"\n📥 [{now}] RAW PAYLOAD: {raw_payload}")

        parts = raw_payload.split(',')
        if len(parts) < 17:
            print(f"⚠️ Malformed payload: {len(parts)}/17 elements found.")
            return

        # 2. Map indices to variables
        duid = parts[0]
        bpm  = parts[1]
        spo2 = parts[2]
        amb_t = parts[3]
        obj_t = parts[4]
        ax, ay, az = parts[5], parts[6], parts[7]
        motion_val = int(parts[8]) 
        is_moving = True if motion_val == 1 else False
        light = parts[9]
        batt_v = parts[10]
        batt_p = parts[11]
        lat, lon = parts[12], parts[13]
        dht_t = parts[14]
        dht_h = parts[15]
        dht_hi = parts[16]

        gps_status = "FIXED"
        if float(lat) == 0.0 or float(lon) == 0.0:
            gps_status = "NO FIX (Saving with 0.0)"

        # 4. Save to Database
        device = Device.objects.get(device_uid=duid)
        record = TelemetryRecord.objects.create(
            device=device,
            is_emergency=False,
            avg_heart_rate=float(bpm) if bpm else 0,
            avg_spo2=float(spo2) if spo2 else 0,
            avg_ambient_temp=float(amb_t),
            avg_object_temp=float(obj_t),
            accel_x=float(ax),
            accel_y=float(ay),
            accel_z=float(az),
            motion_detected=is_moving, 
            light_level=float(light),
            battery_voltage=float(batt_v),
            battery_percentage=int(batt_p),
            latitude=str(lat),
            longitude=str(lon),
            temp_dht22=float(dht_t) if dht_t else None,
            humidity=float(dht_h) if dht_h else None,
            heat_index=float(dht_hi) if dht_hi else None
        )
        
        # Detailed Console Output showing what data is coming
        status_text = "MOVING" if is_moving else "STILL"
        print(f"📊 {duid} | GPS: {gps_status} | Status: {status_text} | HR: {bpm} | Temp: {obj_t}C")
        print(f"🌡️ DHT22: {dht_t}C / {dht_h}% | Batt: {batt_p}%")
        print(f"✅ Record Saved at {timezone.now()}")

        # 5. Live WebSocket Broadcast
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"device_{duid}",
            {
                "type": "telemetry_message",
                "data": {
                    "alert": record.is_emergency,
                    "moving": is_moving,
                    "hr": record.avg_heart_rate,
                    "temp": record.avg_object_temp,
                    "lat": record.latitude,
                    "lon": record.longitude
                },
            }
        )

    except Device.DoesNotExist:
        print(f"⚠️ Unknown Device: {parts[0]}")
    except Exception as e:
        print(f"🔥 Processing Error: {str(e)}")

# --- START SERVICE ---
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print(f"🚀 KTINO CSV Worker Active. Monitoring: {TOPIC}")
client.connect(BROKER, PORT, 60)
client.loop_forever()