import os
import sys
import django
from django.utils import timezone
from django.contrib.gis.geos import Point # Native spatial geometry blueprint constructor
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import paho.mqtt.client as mqtt

# Django system setup synchronization
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ktinoscare.settings")
django.setup()

from telemetry.models import TelemetryRecord, Device

# --- RECONFIGURED CLEAN CONFIGURATION presETS ---
BROKER = os.getenv("MQTT_BROKER_HOST", "mqtt")
PORT = int(os.getenv("MQTT_BROKER_PORT", 1883))
TOPIC = os.getenv("MQTT_TELEMETRY_TOPIC", "ktinoscare/device/+/telemetry")


def on_connect(client, userdata, flags, reason_code, properties=None):
    """Upgraded connection handshake callback validating v2.0 broker responses."""
    if reason_code == 0:
        print(f"✅ Connected to Ingestion Broker [Success] -> Target: {BROKER}:{PORT}")
        client.subscribe(TOPIC)
        print(f"📡 Subscribed to multi-tenant telemetry mask path: {TOPIC}")
    else:
        print(f"❌ Connection Rejected by Broker [Reason Code: {reason_code}]")


def on_message(client, userdata, msg):
    """Processes, validates, maps spatial coordinates, and commits telemetry records."""
    try:
        now = timezone.now()
        raw_payload = msg.payload.decode().strip()
        print(f"\n📥 [{now}] INTERCEPTED RAW WIRE PAYLOAD: {raw_payload}")

        # Extract device information dynamically from the topic structure tree
        # Expected topic format: v1/{species_class}/{device_uid}/telemetry
        topic_segments = msg.topic.split('/')
        if len(topic_segments) < 4:
            print(f"⚠️ Malformed Topic Namespace Ignored: {msg.topic}")
            return
            
        extracted_device_uid = topic_segments[2]

        # Verify hardware identity exists in database before executing storage transactions
        try:
            device_instance = Device.objects.get(device_uid=extracted_device_uid, is_active=True)
        except Device.DoesNotExist:
            print(f"❌ Rejecting unauthorized telemetry payload from unprovisioned ID: {extracted_device_uid}")
            return

        # Split flat positional comma text data block tokens
        parts = [p.strip() for p in raw_payload.split(',')]
        
        # Enforce structural payload size boundaries
        if len(parts) < 27:
            print(f"⚠️ Structural Payload Underflow (Found {len(parts)} parameters, expected 27). Dropping packet.")
            return

        # --- EXTRACT AND CAST PARAMETERS DIRECTLY VIA STRUCTURAL NAMESPACE MAP ---
        timestamp_raw     = int(parts[0])
        is_emergency      = parts[1] in {"1", "true", "TRUE"}
        window_seconds    = int(parts[2])
        
        # Heart Rate Variables
        avg_hr            = float(parts[3]) if parts[3] else None
        min_hr            = float(parts[4]) if parts[4] else None
        max_hr            = float(parts[5]) if parts[5] else None
        
        # SpO2 Variables
        avg_spo2          = float(parts[6]) if parts[6] else None
        min_spo2          = float(parts[7]) if parts[7] else None
        max_spo2          = float(parts[8]) if parts[8] else None
        
        # Temperature Variables
        avg_amb_t         = float(parts[9]) if parts[9] else None
        avg_obj_t         = float(parts[10]) if parts[10] else None
        max_obj_t         = float(parts[11]) if parts[11] else None
        
        # Accelerometer Sensors
        acc_x             = float(parts[12]) if parts[12] else None
        acc_y             = float(parts[13]) if parts[13] else None
        acc_z             = float(parts[14]) if parts[14] else None
        motion_detected   = parts[15] in {"1", "true", "TRUE"}
        light_lvl         = float(parts[16]) if parts[16] else None
        total_steps       = int(parts[17]) if parts[17] else None
        
        # Power parameters
        batt_v            = float(parts[18]) if parts[18] else None
        batt_p            = int(parts[19]) if parts[19] else None
        
        # Coordinates Spatial Frame
        lat_val           = float(parts[20])
        lon_val           = float(parts[21])
        gps_fix_time      = float(parts[22]) if parts[22] else None
        
        # Environmental Parameters
        dht_t             = float(parts[23]) if parts[23] else None
        dht_h             = float(parts[24]) if parts[24] else None
        dht_hi            = float(parts[25]) if parts[25] else None
        rssi_val          = int(parts[26]) if parts[26] else None

        # Build dynamic time-aware partition tracking coordinate
        packet_time = timezone.datetime.fromtimestamp(timestamp_raw, tz=timezone.utc)

        # --- NATIVE POSTGIS GEOMETRY GENERATION MATRIX ---
        # CRITICAL: Point constructor explicitly mandates positional layout order -> Point(longitude, latitude)
        spatial_tracking_point = Point(lon_val, lat_val, srid=4326)

        # Map to TimescaleDB target structure template model
        record = TelemetryRecord(
            device=device_instance,
            is_emergency=is_emergency,
            window_seconds=window_seconds,
            avg_heart_rate=avg_hr,
            min_heart_rate=min_hr,
            max_heart_rate=max_hr,
            avg_spo2=avg_spo2,
            min_spo2=min_spo2,
            max_spo2=max_spo2,
            avg_ambient_temp=avg_amb_t,
            avg_object_temp=avg_obj_t,
            max_object_temp=max_obj_t,
            accel_x=acc_x,
            accel_y=acc_y,
            accel_z=acc_z,
            motion_detected=motion_detected,
            light_level=light_lvl,
            battery_voltage=batt_v,
            battery_percentage=batt_p,
            location=spatial_tracking_point, # Pushes verified spatial objects block natively
            temp_dht22=dht_t,
            humidity=dht_h,
            heat_index=dht_hi,
            created_at=packet_time
        )
        record.save()
        print(f"💾 [DATABASE] TimescaleDB chunk committed cleanly for hardware tracking sequence: {extracted_device_uid}")

        # --- LIVE WEB-SOCKETS MULTICAST DATA PUSH LAYER ---
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"device_{extracted_device_uid}",
            {
                "type": "telemetry_message",
                "data": {
                    "device_uid": extracted_device_uid,
                    "timestamp": packet_time.isoformat(),
                    "avg_heart_rate": avg_hr,
                    "avg_spo2": avg_spo2,
                    "avg_object_temp": avg_obj_t,
                    "motion_detected": motion_detected,
                    "latitude": lat_val,
                    "longitude": lon_val,
                    "battery_percentage": batt_p,
                    "humidity": dht_h,
                    "is_emergency": is_emergency
                },
            }
        )
        print(f"📡 [WEBSOCKET] Multicast broadcast frame pushed successfully to group channel: device_{extracted_device_uid}")

    except Exception as e:
        print(f"🔥 Catastrophic Ingestion Loop Error: {str(e)}")


# --- INITIALIZE PAHO MQTT CLIENT USING STRICT V2.0 CONTRACTS ---
# Declaring explicitly compliance signatures targeting modern message brokers
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()
except KeyboardInterrupt:
    print("\n🛑 Ingestion Consumer Service Interrupted Manually. Shutting down gracefully.")
    sys.exit(0)