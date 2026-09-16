import os
import sys
import json
import urllib.request
import django
from django.utils import timezone
from django.contrib.gis.geos import Point
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import timezone as datetime_timezone
import paho.mqtt.client as mqtt
import logging
from django.db import connection, close_old_connections


# Django system setup synchronization
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ktinoscare.settings")
django.setup()

from telemetry.models import TelemetryRecord, Device
logger = logging.getLogger(__name__)


def _parse_cast(val, cast_type, default=None):
    """Safely cast string values to numeric or boolean types."""
    if val is None or val == "":
        return default
    try:
        if cast_type is bool:
            return val.strip().lower() in {"1", "true", "yes", "t"}
        return cast_type(val.strip())
    except (ValueError, TypeError):
        return default


# --- RECONFIGURED CLEAN CONFIGURATION PRESETS ---
BROKER = os.getenv("MQTT_BROKER_HOST", "mqtt")
PORT = int(os.getenv("MQTT_BROKER_PORT", 1883))
TOPIC = os.getenv("MQTT_TELEMETRY_TOPIC", "ktinoscare/device/+/telemetry")

# Cache resolved IP coordinates so we don't spam the free lookup API on every window
CACHED_FALLBACK_COORDS = None


def get_ip_fallback_coordinates():
    """Resolves approximate latitude and longitude using public IP geolocation."""
    global CACHED_FALLBACK_COORDS
    if CACHED_FALLBACK_COORDS:
        return CACHED_FALLBACK_COORDS
    try:
        req = urllib.request.urlopen("http://ip-api.com/json/?fields=lat,lon,status", timeout=2)
        res = json.loads(req.read().decode())
        if res.get("status") == "success":
            CACHED_FALLBACK_COORDS = (float(res["lat"]), float(res["lon"]))
            return CACHED_FALLBACK_COORDS
    except Exception as e:
        logger.warning(f"⚠️ IP Geolocation fallback lookup failed: {e}")

    # Default fallback: Bengaluru city coordinates
    return (12.9716, 77.5946)


def on_connect(client, userdata, flags, reason_code, properties=None):
    """Upgraded connection handshake callback validating v2.0 broker responses."""
    if reason_code == 0:
        logger.info(f"✅ Connected to Ingestion Broker [Success] -> Target: {BROKER}:{PORT}")
        client.subscribe(TOPIC)
        logger.info(f"📡 Subscribed to multi-tenant telemetry mask path: {TOPIC}")
    else:
        logger.error(f"❌ Connection Rejected by Broker [Reason Code: {reason_code}]")


def on_message(client, userdata, msg):
    """Processes, validates, maps spatial coordinates, and commits telemetry records."""
    # Ensure fresh DB connection state inside long-running MQTT client threads
    close_old_connections()

    try:
        now = timezone.now()
        raw_payload = msg.payload.decode("utf-8", errors="replace").strip()

        # Topic format: ktinoscare/device/{device_uid}/telemetry
        topic_segments = msg.topic.strip("/").split("/")
        if len(topic_segments) < 4:
            logger.warning("Malformed Topic Namespace Ignored: %s", msg.topic)
            return

        extracted_device_uid = topic_segments[2]

        # Verify hardware identity exists and is active
        try:
            device_instance = Device.objects.get(
                device_uid=extracted_device_uid,
                is_active=True
            )
        except Device.DoesNotExist:
            logger.warning(
                "Rejecting unauthorized telemetry payload from unprovisioned ID: %s",
                extracted_device_uid
            )
            return

        # Split positional CSV payload
        parts = [p.strip() for p in raw_payload.split(",")]
        if len(parts) < 27:
            logger.warning(
                "Structural Payload Underflow for %s (Found %d, expected >= 27). Dropping.",
                extracted_device_uid, len(parts)
            )
            return

        # --- EXTRACT AND SAFELY CAST SENSOR PARAMETERS ---
        timestamp_raw   = _parse_cast(parts[0], int, default=int(now.timestamp()))
        is_emergency    = _parse_cast(parts[1], bool, default=False)
        window_seconds  = _parse_cast(parts[2], int, default=300)

        # Heart Rate
        avg_hr          = _parse_cast(parts[3], float)
        min_hr          = _parse_cast(parts[4], float)
        max_hr          = _parse_cast(parts[5], float)

        # SpO2
        avg_spo2        = _parse_cast(parts[6], float)
        min_spo2        = _parse_cast(parts[7], float)
        max_spo2        = _parse_cast(parts[8], float)

        # Temperature
        avg_amb_t       = _parse_cast(parts[9], float)
        avg_obj_t       = _parse_cast(parts[10], float)
        max_obj_t       = _parse_cast(parts[11], float)

        # IMU / Motion / Light
        acc_x           = _parse_cast(parts[12], float)
        acc_y           = _parse_cast(parts[13], float)
        acc_z           = _parse_cast(parts[14], float)
        motion_detected = _parse_cast(parts[15], bool, default=False)
        light_lvl       = _parse_cast(parts[16], float)
        total_steps     = _parse_cast(parts[17], int)

        # Battery / Power
        batt_v          = _parse_cast(parts[18], float)
        batt_p          = _parse_cast(parts[19], int)

        # GPS & Location Coordinates
        lat_val         = _parse_cast(parts[20], float, default=0.0)
        lon_val         = _parse_cast(parts[21], float, default=0.0)
        gps_fix_time    = _parse_cast(parts[22], float)

        # Environmental
        dht_t           = _parse_cast(parts[23], float)
        dht_h           = _parse_cast(parts[24], float)
        dht_hi          = _parse_cast(parts[25], float)
        rssi_val        = _parse_cast(parts[26], int)

        # --- GPS FALLBACK RESOLUTION ---
        if lat_val == 0.0 and lon_val == 0.0:
            try:
                fb_lat, fb_lon = get_ip_fallback_coordinates()
                if fb_lat is not None and fb_lon is not None:
                    lat_val, lon_val = float(fb_lat), float(fb_lon)
            except Exception as coord_err:
                logger.error("IP fallback resolution failed: %s", coord_err)

        # PostGIS expects Point(x, y) -> Point(longitude, latitude)
        spatial_tracking_point = (
            Point(lon_val, lat_val, srid=4326)
            if (lat_val != 0.0 or lon_val != 0.0)
            else None
        )

        packet_time = timezone.datetime.fromtimestamp(
            timestamp_raw, tz=datetime_timezone.utc
        )

        fallback_temp = dht_t if dht_t is not None else avg_amb_t
        fallback_heat_index = dht_hi if dht_hi is not None else avg_amb_t

        # --- PERSIST TELEMETRY RECORD ---
        record = TelemetryRecord.objects.create(
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
            location=spatial_tracking_point,
            temp_dht22=fallback_temp,
            humidity=dht_h,
            heat_index=fallback_heat_index,
            created_at=packet_time,
        )

        # --- REAL-TIME WEBSOCKET BROADCAST ---
        channel_layer = get_channel_layer()
        if channel_layer:
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
                        "is_emergency": is_emergency,
                    },
                },
            )

    except Exception as e:
        logger.exception("Catastrophic Ingestion Loop Error: %s", str(e))
    finally:
        # Prevent database connection leaks across long-lived thread executions
        close_old_connections()

# --- INITIALIZE PAHO MQTT CLIENT USING STRICT V2.0 CONTRACTS ---
client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2)
client.on_connect = on_connect
client.on_message = on_message

try:
    client.connect(BROKER, PORT, keepalive=60)
    client.loop_forever()
except KeyboardInterrupt:
    logger.info("\n🛑 Ingestion Consumer Service Interrupted Manually. Shutting down gracefully.")
    sys.exit(0)