import os
import sys
import json
import paho.mqtt.client as mqtt
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ktinoskare.settings")
django.setup()

from telemetry.models import TelemetryRecord # Adjust based on your actual model name

# Change "localhost" to "mqtt" because inside Docker, 
# services talk to each other by their names in docker-compose.yml
BROKER = "mqtt" 
PORT = 1883
TOPIC = "v1/cattle/+/telemetry"

def on_connect(client, userdata, flags, rc):
    print(f"Connected to Broker with result code: {rc}")
    client.subscribe(TOPIC)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"Received data from {payload.get('device_id')}")

        # Use .create() to save to Postgres
        TelemetryRecord.objects.create(
            device_id=payload["device_id"],
            temperature=payload["temperature"],
            heart_rate=payload["heart_rate"],
        )
    except Exception as e:
        print(f"Error processing message: {e}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

# Using 'mqtt' as the hostname for Docker-to-Docker communication
client.connect(BROKER, PORT, 60)
client.loop_forever()