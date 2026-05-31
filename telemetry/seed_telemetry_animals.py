import random
from datetime import datetime, timedelta
import psycopg2

# --- UNIFIED DEVELOPMENT DATABASE CONNECTION CONFIGURATION ---
DB_NAME = "ktinoscare_db"
DB_USER = "admin"
DB_PASSWORD = "your_secure_password"
DB_HOST = "127.0.0.1"
DB_PORT = "5432"

# Deployed test collars matching your active hardware profile definitions
devices = {
    "KTINO_TEST_001": {"id_num": 1, "lat": 12.9716, "lon": 77.5946},
    "KTINO_TEST_002": {"id_num": 2, "lat": 12.2958, "lon": 76.6394},
}


def generate_records(db_id, device_uid, base_lat, base_lon, start_id):
    """Generates continuous timeseries records with correct PostGIS geometric locations."""
    records = []
    now = datetime.utcnow()
    
    for i in range(25):
        # Evenly spread partitions backward across time chunks
        created_at = now - timedelta(hours=2 * i)
        
        # Add random microscopic jitter to simulate movement shifts
        lat = base_lat + random.uniform(-0.005, 0.005)
        lon = base_lon + random.uniform(-0.005, 0.005)

        # Map physiology variable constraints matching your ktinoscare wearable parameters
        record = (
            start_id + i,                        # id
            random.choice([False, False, True]), # is_emergency
            30,                                  # window_seconds
            random.uniform(65.0, 85.0),          # avg_heart_rate
            random.uniform(55.0, 64.0),          # min_heart_rate
            random.uniform(86.0, 110.0),         # max_heart_rate
            random.uniform(95.0, 99.5),          # avg_spo2
            94.0,                                # min_spo2
            100.0,                               # max_spo2
            random.uniform(24.0, 32.0),          # avg_ambient_temp
            random.uniform(37.5, 39.2),          # avg_object_temp
            40.1,                                # max_object_temp
            random.uniform(-0.2, 0.2),           # accel_x
            random.uniform(-0.2, 0.2),           # accel_y
            random.uniform(0.8, 1.2),            # accel_z
            random.choice([True, False]),        # motion_detected
            random.uniform(150.0, 600.0),        # light_level
            random.uniform(3.7, 4.2),            # battery_voltage
            random.randint(45, 100),             # battery_percentage
            lon,                                 # Geometry Longitude Axis Component
            lat,                                 # Geometry Latitude Axis Component
            random.uniform(22.0, 28.0),          # temp_dht22
            random.uniform(50.0, 75.0),          # humidity
            random.uniform(25.0, 30.0),          # heat_index
            created_at,                          # Timescale partition tracking key
            db_id                                # ForeignKey back to devices_device table
        )
        records.append(record)
    return records


def main():
    print(f"🔌 Initializing connection to cluster database target: [{DB_NAME}]...")
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD,
            host=DB_HOST, port=DB_PORT
        )
        cur = conn.cursor()
        print("🚀 Connected successfully. Commencing raw insertion matrix loops...")

        start_id = 5000
        for uid, info in devices.items():
            print(f"📡 Generating time-series traces for hardware node: {uid}")
            records = generate_records(info["id_num"], uid, info["lat"], info["lon"], start_id)
            
            for rec in records:
                cur.execute("""
                    INSERT INTO public.telemetry_telemetryrecord (
                        id, is_emergency, window_seconds, avg_heart_rate, min_heart_rate, max_heart_rate,
                        avg_spo2, min_spo2, max_spo2, avg_ambient_temp, avg_object_temp, max_object_temp,
                        accel_x, accel_y, accel_z, motion_detected, light_level, battery_voltage,
                        battery_percentage, location, temp_dht22, humidity, heat_index, created_at, device_id
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326), -- FIXED: Formats native PostGIS spatial points explicitly
                        %s, %s, %s, %s, %s
                    );
                """, rec)
            start_id += len(records)
            
        conn.commit()
        print("\n✨ [SUCCESS] 50 historical traces injected successfully across your chunks schema map!")
        
    except Exception as e:
        print(f"\n🔥 Database Insertion Crash: {str(e)}")
    finally:
        if 'conn' in locals():
            cur.close()
            conn.close()


if __name__ == "__main__":
    main()