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
TOPIC = "v1/pet/+/telemetry"

def on_connect(client, userdata, flags, rc):
    print(f"✅ Connected to Broker [Code {rc}]")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        raw_payload = msg.payload.decode().strip()
        d = json.loads(raw_payload) # 'd' for data shortcut
        
        duid = d.get("id")
        msg_type = d.get("t", "TEL") # TEL or ALRT
        
        # 1. GPS Guard Logic (Critical for data integrity)
        lat = d.get("la", 0.0)
        lon = d.get("lo", 0.0)
        if float(lat) == 0.0 or float(lon) == 0.0:
            print(f"📍 {duid}: Skipping record (Waiting for GPS lock...)")
            return

        # 2. Database Save with Mapping
        device = Device.objects.get(device_uid=duid)
        record = TelemetryRecord.objects.create(
            device=device,
            is_emergency=(msg_type == "ALRT"),
            window_seconds=d.get("w", 30),
            
            avg_heart_rate=d.get("ahr"),
            min_heart_rate=d.get("nhr"),
            max_heart_rate=d.get("mhr"),
            
            avg_spo2=d.get("as2"),
            avg_ambient_temp=d.get("aat"),
            avg_object_temp=d.get("aot"),
            max_object_temp=d.get("mot"),
            
            accel_x=d.get("ax"),
            accel_y=d.get("ay"),
            accel_z=d.get("az"),
            motion_detected=d.get("m", False),
            light_level=d.get("l"),
            battery_voltage=d.get("bv"),
            battery_percentage=d.get("bp"),
            latitude=str(lat),
            longitude=str(lon),
        )
        
        print(f"📊 {duid}: Saved {'ALERT' if record.is_emergency else 'Telemetry'} at {timezone.now()}")

        # 3. WebSocket Broadcast (Keeping the frontend fast)
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
        print(f"⚠️ Error: Unknown Device {d.get('id')}")
    except Exception as e:
        print(f"🔥 Error: {str(e)}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print(f"🚀 KTINO Multi-Pet Worker Active. Monitoring topics: {TOPIC}")
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