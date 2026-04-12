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
        # 1. Decode CSV string from ESP32 
        raw_payload = msg.payload.decode().strip()
        parts = raw_payload.split(',')
        
        if len(parts) < 14:
            print(f"⚠️ Malformed payload: {len(parts)} elements found.")
            return

        # 2. Map indices to variables 
        duid = parts[0]   # device_uid
        bpm  = parts[1]   # avg_heart_rate
        spo2 = parts[2]   # avg_spo2
        amb_t = parts[3]  # avg_ambient_temp
        obj_t = parts[4]  # avg_object_temp
        ax, ay, az = parts[5], parts[6], parts[7]
        light = parts[9]
        batt_v = parts[10]
        batt_p = parts[11]
        lat, lon = parts[12], parts[13]
        dht_t = parts[14]
        dht_h = parts[15]
        dht_hi = parts[16]

        # 3. GPS Guard
        if float(lat) == 0.0 or float(lon) == 0.0:
            print(f"📍 {duid}: Skipping (Waiting for GPS lock...)")
            return

        # 4. Save to Database
        device = Device.objects.get(device_uid=duid)
        record = TelemetryRecord.objects.create(
            device=device,
            is_emergency=False,
            avg_heart_rate=float(bpm),
            avg_spo2=float(spo2),
            avg_ambient_temp=float(amb_t),
            avg_object_temp=float(obj_t),
            accel_x=float(ax),
            accel_y=float(ay),
            accel_z=float(az),
            light_level=float(light),
            battery_voltage=float(batt_v),
            battery_percentage=int(batt_p),
            latitude=str(lat),
            longitude=str(lon),
            temp_dht22=float(dht_t) if dht_t else None,
            humidity=float(dht_h) if dht_h else None,
            heat_index=float(dht_hi) if dht_hi else None
        )
        
        print(f"📊 {duid}: Record Saved from Jammu Pilot at {timezone.now()}")

        # 5. Live WebSocket Broadcast
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"device_{duid}",
            {
                "type": "telemetry_message",
                "data": {
                    "alert": record.is_emergency,
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
        print(f"🔥 Error: {str(e)}")

# --- START SERVICE ---
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print(f"🚀 KTINO CSV Worker Active. Monitoring: {TOPIC}")
client.connect(BROKER, PORT, 60)
client.loop_forever()



# import os
# import sys
# import json
# import paho.mqtt.client as mqtt
# import django
# from datetime import datetime
# from django.utils import timezone
# from channels.layers import get_channel_layer
# from asgiref.sync import async_to_sync

# # Django setup
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ktinoskare.settings")
# django.setup()

# from telemetry.models import TelemetryRecord, Device

# BROKER = "mqtt"
# PORT = 1883
# TOPIC = "v1/pet/+/telemetry" # Updated topic for "All Pets"

# def on_connect(client, userdata, flags, rc):
#     print(f"Connected to Broker with result code: {rc}")
#     client.subscribe(TOPIC)

# def on_message(client, userdata, msg):
#     try:
#         raw_payload = msg.payload.decode().strip()
#         data = json.loads(raw_payload) # Switching to JSON
        
#         device_uid = data.get("duid")
#         msg_type = data.get("type", "TELEMETRY") # ALERT or TELEMETRY
        
#         print(f"\n--- [{msg_type}] FROM {device_uid} ---")

#         device = Device.objects.get(device_uid=device_uid)

#         # Create DB Record with Min/Max/Avg
#         record = TelemetryRecord.objects.create(
#             device=device,
#             is_emergency=(msg_type == "ALERT"),
#             window_seconds=data.get("window", 30),
            
#             avg_heart_rate=data.get("avg_hr"),
#             min_heart_rate=data.get("min_hr"),
#             max_heart_rate=data.get("max_hr"),
            
#             avg_spo2=data.get("avg_spo2"),
#             min_spo2=data.get("min_spo2"),
#             max_spo2=data.get("max_spo2"),
            
#             avg_ambient_temp=data.get("avg_amb_t"),
#             avg_object_temp=data.get("avg_obj_t"),
#             max_object_temp=data.get("max_obj_t"),
            
#             accel_x=data.get("ax"),
#             accel_y=data.get("ay"),
#             accel_z=data.get("az"),
#             motion_detected=data.get("motion", False),
#             light_level=data.get("light"),
#             battery_voltage=data.get("batt_v"),
#             battery_percentage=data.get("batt_pct"),
#             latitude=str(data.get("lat")),
#             longitude=str(data.get("lon")),
#         )
#         print(f"✅ Record Saved. ID: {record.id}")

#         # Broadcast to WebSocket
#         channel_layer = get_channel_layer()
#         group_name = f"device_{device_uid}"
        
#         async_to_sync(channel_layer.group_send)(
#             group_name,
#             {
#                 "type": "telemetry_message",
#                 "data": {
#                     "is_emergency": record.is_emergency,
#                     "avg_hr": record.avg_heart_rate,
#                     "avg_obj_t": record.avg_object_temp,
#                     "lat": record.latitude,
#                     "lon": record.longitude,
#                     "timestamp": record.created_at.isoformat()
#                 },
#             }
#         )

#     except Device.DoesNotExist:
#         print(f"❌ Error: Device {device_uid} not found in DB.")
#     except Exception as e:
#         print(f"🔥 Processing Error: {e}")

# client = mqtt.Client()
# client.on_connect = on_connect
# client.on_message = on_message

# print(f"KTINO Worker Started. Listening for all pets...")
# client.connect(BROKER, PORT, 60)
# client.loop_forever()