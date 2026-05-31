import paho.mqtt.publish as publish

# FIXED: Aligned to match the precise topic pattern: v1/{species}/{device_uid}/telemetry
TARGET_TOPIC = "v1/ktinoscare/KTINO_TEST_001/telemetry"

# FIXED: Transmits the full 27 positional parameter string required by the parsed schema map
MOCK_CSV_ROW = "1778930400,0,30,74.2,69.0,82.5,97.1,95.0,99.0,39.4,38.8,39.1,0.05,-0.09,0.97,1,412.5,142,4.12,96,12.9716,77.5946,4.8,40.5,62.3,43.8,-68"

print(f"📡 Launching mock payload vector down to broker -> {TARGET_TOPIC}")
publish.single(
    TARGET_TOPIC,
    MOCK_CSV_ROW,
    hostname="localhost",
    port=1883
)
print("🚀 Transmission successfully processed.")