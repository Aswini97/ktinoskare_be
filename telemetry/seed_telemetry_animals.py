import random
from datetime import datetime, timedelta
import psycopg2

# Database connection settings
DB_NAME = "cattle_db"
DB_USER = "admin"
DB_PASSWORD = "your_secure_password"
DB_HOST = "db"
DB_PORT = "5432"

# KTINO devices (device_id must match your devices_device table)
devices = {
    8: ("KTINO_001", "12.9716", "77.5946"),  # Falcon
    9: ("KTINO_002", "12.2958", "76.6394"),  # Wolf
    10: ("KTINO_003", "11.0168", "76.9558"),  # Bear
    11: ("KTINO_004", "13.0827", "80.2707"),  # Eagle
    12: ("KTINO_005", "15.2993", "74.1240"),  # Fox
}

def generate_records(device_id, lat, lon, start_id):
    """Generate 25 telemetry records for one device with animal physiology ranges."""
    records = []
    now = datetime.now()
    for i in range(25):
        created_at = now - timedelta(hours=6 * i)  # spread across ~7 days

        # Animal physiology ranges
        heart_rate = random.randint(40, 90)  # bpm
        spo2 = random.randint(95, 100)       # %
        ambient_temp = round(random.uniform(20.0, 35.0), 1)  # °C
        object_temp = round(random.uniform(37.0, 39.5), 1)   # °C
        accel_x = round(random.uniform(-0.2, 0.2), 2)
        accel_y = round(random.uniform(-0.2, 0.2), 2)
        accel_z = round(random.uniform(9.7, 9.9), 2)
        battery_voltage = round(random.uniform(3.6, 4.1), 2)
        battery_percentage = random.randint(40, 95)
        light_level = round(random.uniform(0.5, 2.0), 2)
        motion_detected = random.choice([True, False])

        record = (
            start_id + i,
            heart_rate,
            ambient_temp,
            lat,
            lon,
            battery_voltage,
            created_at,
            device_id,
            accel_x,
            accel_y,
            accel_z,
            battery_percentage,
            light_level,
            motion_detected,
            object_temp,
            spo2,
        )
        records.append(record)
    return records

def main():
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
        host=DB_HOST, port=DB_PORT
    )
    cur = conn.cursor()

    start_id = 1001
    for device_id, (_, lat, lon) in devices.items():
        records = generate_records(device_id, lat, lon, start_id)
        for rec in records:
            cur.execute("""
                INSERT INTO public.telemetry_telemetryrecord
                (id, heart_rate, ambient_temperature, latitude, longitude,
                 battery_voltage, created_at, device_id, accel_x, accel_y, accel_z,
                 battery_percentage, light_level, motion_detected, object_temperature, spo2)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, rec)
        start_id += 25  # increment ID range for next device

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Seeded 25 animal telemetry records per KTINO device (125 total).")

if __name__ == "__main__":
    main()