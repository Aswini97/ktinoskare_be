import paho.mqtt.publish as publish

publish.single(
    "v1/cattle/ABC123/telemetry",
    "ABC123,72,98,25.0,37.5,0.1,0.2,0.3,1,300,3.7,95,12.9716,77.5946",
    hostname="localhost",
    port=1883
)