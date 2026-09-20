import os
import sys
import math
import random
from datetime import datetime, timedelta, timezone as dt_timezone
from pathlib import Path

# Add project root directory (/app) to sys.path regardless of script location
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Matches the exact configuration module in manage.py
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ktinoskare.settings")

import django
django.setup()

from django.contrib.gis.geos import Point
from telemetry.models import TelemetryRecord, Device

# --- COORDINATES CONVERTED TO DECIMAL DEGREES ---
# 12°56'21.1"N 77°43'45.8"E (Bengaluru, Karnataka)
BENGALURU_LAT = 12.939194
BENGALURU_LON = 77.729389

# 32°44'47.7"N 74°52'05.0"E (Jammu, J&K)
JAMMU_LAT = 32.746583
JAMMU_LON = 74.868056

WINDOW_SECONDS = 300  # 5-minute sampling interval (matching production firmware)
DAYS_TO_GENERATE = 30
BATCH_SIZE = 1000

# Canine profile definitions
DOG_PROFILES = [
    {
        "device_uid": "KTINO_79E14C", # Change to your actual first device_uid if different
        "breed": "Doberman Pinscher (4yo, Large)",
        "base_lat": BENGALURU_LAT,
        "base_lon": BENGALURU_LON,
        "resting_hr": 72.0,
        "active_hr_max": 145.0,
        "base_obj_temp": 38.3,
        "climate_temp_avg": 24.0, # Bengaluru ambient
        "climate_temp_amp": 5.0,
    },
    {
        "device_uid": "KTINO_A9F68C", # Change to your actual second device_uid if different
        "breed": "Indian Pariah Dog (2.5yo, Medium)",
        "base_lat": JAMMU_LAT,
        "base_lon": JAMMU_LON,
        "resting_hr": 88.0,
        "active_hr_max": 160.0,
        "base_obj_temp": 38.6,
        "climate_temp_avg": 27.0, # Jammu ambient
        "climate_temp_amp": 8.0,
    }
]


def generate_canine_telemetry():
    now = datetime.now(dt_timezone.utc)
    start_time = now - timedelta(days=DAYS_TO_GENERATE)
    total_steps = int((DAYS_TO_GENERATE * 86400) / WINDOW_SECONDS)

    print(f"🚀 Generating ~{total_steps * 2:,} realistic telemetry records over {DAYS_TO_GENERATE} days...")

    for profile in DOG_PROFILES:
        try:
            device = Device.objects.get(device_uid=profile["device_uid"])
        except Device.DoesNotExist:
            print(f"⚠️ Device '{profile['device_uid']}' not found in Device table. Skipping this device.")
            continue

        print(f"\n🐕 Simulating profile for {profile['breed']} [UID: {profile['device_uid']}]...")

        battery_pct = 98.0
        cumulative_steps = random.randint(1000, 5000)
        records_buffer = []

        # Coordinate random-walk drift memory during outdoor excursions
        current_lat = profile["base_lat"]
        current_lon = profile["base_lon"]

        for step_idx in range(total_steps):
            packet_time = start_time + timedelta(seconds=step_idx * WINDOW_SECONDS)
            hour = packet_time.hour + (packet_time.minute / 60.0)

            # --- 1. CIRCADIAN PHASE MODELING ---
            # Walk windows: 07:00 - 08:30 and 18:00 - 19:30
            is_morning_walk = 7.0 <= hour <= 8.5
            is_evening_walk = 18.0 <= hour <= 19.5
            is_active_walk = is_morning_walk or is_evening_walk

            # Deep sleep: 22:00 - 06:30; Nap: 13:00 - 15:30
            is_deep_sleep = (hour >= 22.0 or hour < 6.5)
            is_afternoon_nap = (13.0 <= hour <= 15.5)
            is_sleeping = is_deep_sleep or is_afternoon_nap

            # --- 2. ACTIVITY & ACCELERATION ---
            if is_active_walk:
                motion_detected = True
                steps_in_window = random.randint(180, 480)
                # Dynamic motion vector (dog trotting/running)
                accel_x = round(random.gauss(0.15, 0.45), 3)
                accel_y = round(random.gauss(0.20, 0.55), 3)
                accel_z = round(random.gauss(0.95, 0.35), 3)
            elif is_sleeping:
                motion_detected = random.random() < 0.08 # Rare position adjustment
                steps_in_window = random.randint(0, 4) if motion_detected else 0
                # Lying down on belly/side: dominant axis aligned with gravity
                accel_x = round(random.gauss(0.02, 0.04), 3)
                accel_y = round(random.gauss(-0.85, 0.06), 3) if random.random() < 0.5 else round(random.gauss(0.05, 0.05), 3)
                accel_z = round(random.gauss(0.50, 0.08), 3)
            else:
                # Awake indoors: pacing, looking around, resting
                motion_detected = random.random() < 0.35
                steps_in_window = random.randint(15, 80) if motion_detected else random.randint(0, 5)
                accel_x = round(random.gauss(0.05, 0.15), 3)
                accel_y = round(random.gauss(0.10, 0.20), 3)
                accel_z = round(random.gauss(0.98, 0.10), 3)

            cumulative_steps += steps_in_window

            # --- 3. BIOMETRICS (HEART RATE & TEMPERATURE) ---
            if is_active_walk:
                target_hr = random.uniform(profile["resting_hr"] + 40, profile["active_hr_max"])
            elif is_sleeping:
                target_hr = random.gauss(profile["resting_hr"], 3.0)
            else:
                target_hr = random.uniform(profile["resting_hr"] + 5, profile["resting_hr"] + 25)

            avg_hr = round(target_hr, 1)
            min_hr = round(avg_hr - random.uniform(2.0, 7.0), 1)
            max_hr = round(avg_hr + random.uniform(3.0, 10.0), 1)

            # Normal canine SpO2: 96.0% - 99.5%
            avg_spo2 = round(min(99.8, max(95.5, random.gauss(98.1, 0.7))), 1)
            min_spo2 = round(avg_spo2 - random.uniform(0.5, 1.8), 1)
            max_spo2 = round(min(100.0, avg_spo2 + random.uniform(0.2, 1.2)), 1)

            # Ambient and surface temperatures
            diurnal_ambient_swing = profile["climate_temp_amp"] * math.sin(math.pi * (hour - 9.0) / 12.0)
            avg_amb_t = round(profile["climate_temp_avg"] + diurnal_ambient_swing + random.gauss(0, 0.6), 1)
            avg_obj_t = round(profile["base_obj_temp"] + (0.4 if is_active_walk else 0.0) + random.gauss(0, 0.15), 1)
            max_obj_t = round(avg_obj_t + random.uniform(0.1, 0.4), 1)

            # Humidity & Heat Index simulation
            humidity = round(max(35.0, min(85.0, 60.0 - (diurnal_ambient_swing * 2.0) + random.gauss(0, 2.0))), 1)
            heat_index = round(avg_amb_t + (0.1 * humidity / 10.0), 1)

            # Light level tracking daylight (Lux)
            if 6.0 <= hour <= 18.5:
                sun_curve = math.sin(math.pi * (hour - 6.0) / 12.5)
                light_lvl = round(max(10.0, sun_curve * 850.0 + random.gauss(0, 30.0)), 1) if is_active_walk else round(sun_curve * 220.0 + random.gauss(0, 15.0), 1)
            else:
                light_lvl = round(max(0.0, random.gauss(2.0, 1.5)), 1) # Indoor room / nighttime darkness

            # --- 4. GEOGRAPHIC SPATIAL PATH ---
            if is_active_walk:
                # Walk displacement: smoothly drifts up to 400m around neighborhood
                walk_angle = (step_idx % 30) * (2 * math.pi / 30)
                walk_radius = random.uniform(0.0008, 0.0035) # ~100m to 400m
                current_lat = profile["base_lat"] + (walk_radius * math.cos(walk_angle)) + random.gauss(0, 0.00004)
                current_lon = profile["base_lon"] + (walk_radius * math.sin(walk_angle)) + random.gauss(0, 0.00004)
            else:
                # Indoors: tight jitter around home base (~3-8 meters indoor multipath error)
                current_lat = profile["base_lat"] + random.gauss(0, 0.00003)
                current_lon = profile["base_lon"] + random.gauss(0, 0.00003)

            location_point = Point(round(current_lon, 6), round(current_lat, 6), srid=4326)

            # --- 5. BATTERY DRAIN & RECHARGE CYCLE ---
            # Collar battery discharges over ~84 hours (3.5 days), then charges for 2.5 hours
            battery_pct -= (100.0 / (84.0 * 12.0))
            if battery_pct <= 12.0:
                battery_pct = 100.0 # Recharged to full

            batt_p = int(round(battery_pct))
            batt_v = round(3.45 + (battery_pct / 100.0) * 0.75, 2) # 3.45V to 4.20V Li-ion range

            # Telemetry record construct
            record = TelemetryRecord(
                device=device,
                is_emergency=False,
                window_seconds=WINDOW_SECONDS,
                avg_heart_rate=avg_hr,
                min_heart_rate=min_hr,
                max_heart_rate=max_hr,
                avg_spo2=avg_spo2,
                min_spo2=min_spo2,
                max_spo2=max_spo2,
                avg_ambient_temp=avg_amb_t,
                avg_object_temp=avg_obj_t,
                max_object_temp=max_obj_t,
                accel_x=accel_x,
                accel_y=accel_y,
                accel_z=accel_z,
                motion_detected=motion_detected,
                light_level=light_lvl,
                battery_voltage=batt_v,
                battery_percentage=batt_p,
                location=location_point,
                temp_dht22=avg_amb_t,
                humidity=humidity,
                heat_index=heat_index,
                created_at=packet_time
            )
            records_buffer.append(record)

            # Batch insert to avoid memory bloat
            if len(records_buffer) >= BATCH_SIZE:
                TelemetryRecord.objects.bulk_create(records_buffer)
                records_buffer.clear()
                print(f"  ⚡ Ingested batch at {packet_time.strftime('%Y-%m-%d %H:%M UTC')}...")

        if records_buffer:
            TelemetryRecord.objects.bulk_create(records_buffer)
            records_buffer.clear()

        print(f"✅ Finished generating 30 days of data for {profile['breed']}.")

    print("\n🎉 All synthetic telemetry generated and committed successfully!")


if __name__ == "__main__":
    generate_canine_telemetry()