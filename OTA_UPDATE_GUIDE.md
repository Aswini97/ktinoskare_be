Create this reference document (e.g., `OTA_UPDATE_GUIDE.md`) in your project repository:

```markdown
# ESP32 Over-The-Air (OTA) Update Guide

This runbook outlines the process for building, deploying, and triggering remote firmware updates for KtinosCare livestock collar devices.

---

## 1. Prerequisites & Firmware Configuration

Before compiling a new firmware version, verify the following settings:

* **Partition Scheme**: In the Arduino IDE, navigate to `Tools` -> `Partition Scheme` and select:
  ```text
  Minimal SPIFFS (1.9MB APP with OTA/128KB SPIFFS)
```

*(This reserves dual 1.9MB application partitions (`app0` and `app1`) and preserves LittleFS for non-volatile configuration).*

* **Firmware Version Increment**: In the `.ino` sketch, increment `CURRENT_FIRMWARE_VERSION` to match the target release:
```cpp
#define CURRENT_FIRMWARE_VERSION "1.0.1"
```



---

## 2. Exporting the Compiled Binary

1. Open the sketch in **Arduino IDE 2.x**.
2. Click **Sketch** -> **Export Compiled Binary** (`Ctrl + Alt + S`).
3. Arduino IDE will generate a `.bin` file inside the `build/` folder within your sketch directory (e.g., `build/esp32.esp32.esp32da/pet_monitor_code_v6.ino.bin`).
4. Rename the binary to match your versioning standard:
```text
firmware_v1.0.1.bin
```



---

## 3. Uploading Binary to Nginx Firmware Storage

Transfer the binary to the Nginx static firmware directory on your AWS EC2 instance:

```bash
scp -i /path/to/your-key.pem firmware_v1.0.1.bin ubuntu@13.233.104.107:~/ktinoskare_be/nginx/firmware/
```

Verify that the file is readable by the Nginx container:

```bash
# Verify file exists on host
ls -la ~/ktinoskare_be/nginx/firmware/

# Reload Nginx configuration if needed
docker compose exec nginx nginx -s reload
```

---

## 4. Validating Direct Binary Download

Test that the binary is reachable over plain HTTP without redirects:

```bash
curl -I [http://13.233.104.107/firmware/firmware_v1.0.1.bin](http://13.233.104.107/firmware/firmware_v1.0.1.bin)
```

**Expected Response:**

```http
HTTP/1.1 200 OK
Content-Length: 1154704
Content-Type: application/octet-stream
```

*(Ensure the response is `200 OK` and not a `301 Moved Permanently` to HTTPS).*

---

## 5. Triggering the OTA Update via API

Send an HTTP POST request to the backend OTA trigger endpoint using Postman or `curl`:

```bash
curl -X POST [https://13.233.104.107/api/v1/devices/KTINO_79E14C/ota/](https://13.233.104.107/api/v1/devices/KTINO_79E14C/ota/) \
  -H "Content-Type: application/json" \
  -d '{
    "version": "1.0.1",
    "url": "[http://13.233.104.107/firmware/firmware_v1.0.1.bin](http://13.233.104.107/firmware/firmware_v1.0.1.bin)"
  }'
```

**Expected Response:**

```json
{
  "status": "success",
  "message": "OTA update command published successfully to ktinoscare/device/KTINO_79E14C/cmd",
  "payload": {
    "action": "ota_update",
    "version": "1.0.1",
    "url": "[http://13.233.104.107/firmware/firmware_v1.0.1.bin](http://13.233.104.107/firmware/firmware_v1.0.1.bin)"
  }
}
```

---

## 6. Verifying Device Update Status

Run the following checks from your EC2 instance to verify the update lifecycle:

### Step A: Verify Binary Download in Nginx Logs

```bash
docker compose logs --tail=20 nginx | grep "firmware_v1.0.1.bin"
```

*Look for:*
`"GET /firmware/firmware_v1.0.1.bin HTTP/1.0" 200 1154704 "-" "ESP32-http-Update"`

### Step B: Monitor Device Reconnection in Worker Logs

```bash
docker compose logs -f --tail=20 mqtt_worker
```

*Look for live telemetry returning after a ~15-second reboot cycle:*
`📥 [...] INTERCEPTED RAW WIRE PAYLOAD: KTINO_79E14C,...`

### Step C: Verify Database Ingestion

```bash
docker compose exec db psql -U admin -d ktinoscare_db -c "
SELECT d.device_uid, t.created_at, t.battery_percentage, t.avg_heart_rate 
FROM devices_device d 
JOIN telemetry_telemetryrecord t ON d.id = t.device_id 
WHERE d.device_uid = 'KTINO_79E14C' 
ORDER BY t.created_at DESC 
LIMIT 3;
"
```

---

## 7. Troubleshooting Common Issues

* **Device Enters Download Loop**: Ensure `CURRENT_FIRMWARE_VERSION` in the compiled binary matches the target `"version"` sent in the OTA JSON command.
* **Retained MQTT Messages**: If the device continuously re-downloads, clear retained command messages in EMQX:
```bash
docker compose exec mqtt emqx ctl retainer clean "ktinoscare/device/KTINO_79E14C/cmd"
```


* **Download Fails (`301 Moved Permanently`)**: Ensure the payload URL uses `http://` instead of `https://`.

```
<Elicitations message="What would you like to configure next?">
  <Elicitation label="Add firmware version to telemetry" query="How can I update the telemetry payload format so the ESP32 reports its active firmware version to the database?"/>
  <Elicitation label="Configure S3 OTA storage" query="How do I configure Django and Nginx to serve firmware binaries from an AWS S3 bucket instead of the local server filesystem?"/>
</Elicitations>
```