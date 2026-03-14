import json
import paho.mqtt.client as mqtt
import django
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ktinoskare.settings")
django.setup()

from telemetry.models import Telemetry


BROKER = "localhost"
PORT = 1883
TOPIC = "collar/+/telemetry"


def on_connect(client, userdata, flags, rc):
    print("Connected:", rc)
    client.subscribe(TOPIC)


def on_message(client, userdata, msg):

    payload = json.loads(msg.payload.decode())

    Telemetry.objects.create(
        device_id=payload["device_id"],
        temperature=payload["temperature"],
        heart_rate=payload["heart_rate"],
        timestamp=payload["timestamp"]
    )


client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER, PORT, 60)

client.loop_forever()