This is Ktinoskare Backend, created with Python Django Framework.

## Testing Telemetry Flow (MQTT → WebSocket)

This document covers testing the complete telemetry data flow from MQTT broker to WebSocket clients.

### Architecture Overview

```
IoT Device → MQTT Broker → mqtt_consumer (Django) → Redis Channel Layer → WebSocket → Browser
```

**Key Components:**
- `mqtt_consumer.py` - Subscribes to MQTT, saves to database, broadcasts via WebSocket
- `socket_consumer.py` - WebSocket handler that joins device groups and forwards telemetry
- `redis` - Channel layer for broadcasting messages between Django and WebSocket

### Prerequisites

Ensure all services are running:

```bash
docker-compose up -d
```

Verify services:
```bash
docker-compose ps
# Should show: db, mqtt, mqtt_worker, web, pgadmin, redis all with status "running"
```

### Test Your Device

Your devices must exist in the database before sending telemetry. Example device UID: `KTINO_001`, `KTINO_002`

### 1. Send MQTT Test Message

Publish telemetry data to MQTT broker:

```bash
docker exec -it ktinoskare_be-mqtt-1 mosquitto_pub -t "v1/cattle/KTINO_002/telemetry" -m "KTINO_002,80,98,28.5,32.2,0.1,0.2,9.8,1,1.5,4.0,90,12.9716,77.5946"
```

**CSV Format Breakdown:**
```
KTINO_002,    # Device UID
80,           # Heart Rate (bpm)
98,           # SpO2 (%)
28.5,         # Ambient Temperature (°C)
32.2,         # Object Temperature (°C)
0.1,          # Accel X (m/s²)
0.2,          # Accel Y (m/s²)
9.8,          # Accel Z (m/s²)
1,            # Motion Detected (0/1)
1.5,          # Light Level (lux)
4.0,          # Battery Voltage (V)
90,           # Battery Percentage (%)
12.9716,      # Latitude
77.5946       # Longitude
```

**Valid GPS Coordinates** (non-zero required):
- `12.9716, 77.5946` - Bangalore, India
- `40.7128, -74.0060` - New York, USA
- Your actual device coordinates

**⚠️ Note:** If latitude or longitude is 0.0, the message is skipped (GPS not acquired).

### 2. Verify MQTT Message Received

Check mqtt_worker logs:

```bash
docker-compose logs mqtt_worker --tail=20
```

**Expected Output:**
```
--- INCOMING TELEMETRY [2026-03-25 11:45:35] ---
RAW: KTINO_002,80,98,28.5,32.2,0.1,0.2,9.8,1,1.5,4.0,90,12.9716,77.5946
DEBUG -> Lat: 12.9716 | Lon: 77.5946
✅ SUCCESS: Record saved for KTINO_002
📡 Channel Layer: <built-in object>
📡 Broadcasting to group: device_KTINO_002
📡 Broadcast sent successfully to device_KTINO_002
```

### 3. Test WebSocket Connection

**Option A: Using HTML Test Client (Easiest)**

1. Open the HTML test page in your browser:
   ```
   d:\Ktinoskare\ktinoskare_be\test_websocket.html
   ```

2. Fill in the form:
   - **Device UID:** `KTINO_002`
   - **Device ID:** `2` (numeric ID from URL)

3. Click **Connect**

4. You should see in the log:
   ```
   ✅ WebSocket Connected!
   Sending subscription: {"duid": "KTINO_002"}
   📨 Received: {"ok": true}
   ```

5. Publish MQTT message (from Step 1)

6. **Expected WebSocket message:**
   ```json
   {
     "telemetry": {
       "duid": "KTINO_002",
       "lat": 12.9716,
       "long": 77.5946,
       "hr": 80,
       "spo2": 98,
       "amb_temp": 28.5,
       "obj_temp": 32.2,
       "ax": 0.1,
       "ay": 0.2,
       "az": 9.8,
       "motion": true,
       "light": 1.5,
       "batt_v": 4.0,
       "batt_pct": 90
     }
   }
   ```

**Option B: Using JavaScript/Frontend**

Connect to WebSocket with:
```javascript
// Create WebSocket connection
const ws = new WebSocket("ws://localhost/ws/telemetry/2/");

ws.onopen = () => {
  // Subscribe to device
  ws.send(JSON.stringify({"duid": "KTINO_002"}));
};

ws.onmessage = (event) => {
  console.log("Telemetry received:", JSON.parse(event.data));
};

ws.onerror = (error) => {
  console.error("WebSocket Error:", error);
};
```

### WebSocket API Specification

**Connection:**
```
ws://localhost/ws/telemetry/{device_id}/
```

**Subscribe to Device:**
```json
{"duid": "KTINO_001"}
```

**Response:**
```json
{"ok": true}
```

**Telemetry Data (Real-time):**
```json
{
  "telemetry": {
    "duid": "string",
    "lat": number,
    "long": number,
    "hr": number,
    "spo2": number,
    "amb_temp": number,
    "obj_temp": number,
    "ax": number,
    "ay": number,
    "az": number,
    "motion": boolean,
    "light": number,
    "batt_v": number,
    "batt_pct": number
  }
}
```

**Heartbeat (every 30s):**
```json
{"heartbeat": true}
```

### Troubleshooting

**"WebSocket Error" in browser console:**
- Check if port 80 is accessible (Docker port mapping)
- Verify `docker-compose ps` shows `web` service running
- Clear browser cache (Ctrl+F5)

**MQTT message not received:**
```bash
docker-compose logs mqtt --tail=20
docker-compose logs mqtt_worker --tail=20
```

**No telemetry on WebSocket:**
1. Verify device exists in database
2. Check that `duid` matches device UID exactly
3. Verify Redis is running: `docker-compose logs redis`

**Device not found error:**
```bash
# Check device UID in database
docker-compose exec db psql -U admin -d cattle_db -c "SELECT device_uid FROM devices_device;"
```

### Full End-to-End Test

```bash
# 1. Start all services
docker-compose up -d

# 2. Check services are healthy
docker-compose ps

# 3. Publish MQTT message
docker exec -it ktinoskare_be-mqtt-1 mosquitto_pub -t "v1/cattle/KTINO_001/telemetry" -m "KTINO_001,75,96,26.0,30.5,0.05,0.15,9.8,0,2.0,4.1,88,40.7128,-74.0060"

# 4. Check MQTT consumer processed it
docker-compose logs mqtt_worker --tail=15

# 5. Open test_websocket.html in browser and connect
# 6. Publish another MQTT message
# 7. Verify telemetry appears in WebSocket log
```

---

## WebSocket Connection Guide

### Connection Basics

**WebSocket URL:**
```
ws://localhost/ws/telemetry/{device_id}/
```

**Parameters:**
- `device_id` - Numeric ID from the devices table (e.g., `1`, `2`, `3`)
- Port: `80` (mapped from Docker container port 8000)

### Step 1: Establish Connection

**Plain JavaScript:**
```javascript
const deviceId = 2; // Your device numeric ID
const ws = new WebSocket(`ws://localhost/ws/telemetry/${deviceId}/`);

ws.onopen = () => {
  console.log("✅ Connected to WebSocket");
};

ws.onerror = (error) => {
  console.error("❌ Connection Error:", error);
};

ws.onclose = () => {
  console.log("❌ WebSocket Closed");
};
```

### Step 2: Subscribe to Device

After connection, send subscription message:

```javascript
ws.onopen = () => {
  // Subscribe to specific device using device UID
  ws.send(JSON.stringify({
    "duid": "KTINO_002"  // Device UID from your database
  }));
};
```

**Response:**
```json
{"ok": true}
```

### Step 3: Handle Incoming Messages

```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  // Check message type
  if (message.telemetry) {
    console.log("📡 Telemetry Data:", message.telemetry);
    handleTelemetryData(message.telemetry);
  }

  if (message.heartbeat) {
    console.log("💓 Heartbeat received");
  }

  if (message.ok) {
    console.log("✅ Subscription confirmed");
  }

  if (message.error) {
    console.error("⚠️ Error:", message.error);
  }
};
```

### Message Types

#### 1. Connection Acknowledgment
```json
{"ok": true}
```
Sent immediately after WebSocket connection established.

#### 2. Subscription Confirmation
```json
{"ok": true}
```
Sent after subscribing with `duid`.

#### 3. Telemetry Data (Real-time from MQTT)
```json
{
  "telemetry": {
    "duid": "KTINO_002",
    "lat": 12.9716,
    "long": 77.5946,
    "hr": 80,
    "spo2": 98,
    "amb_temp": 28.5,
    "obj_temp": 32.2,
    "ax": 0.1,
    "ay": 0.2,
    "az": 9.8,
    "motion": true,
    "light": 1.5,
    "batt_v": 4.0,
    "batt_pct": 90
  }
}
```

**Field Reference:**
| Field | Type | Description | Unit |
|-------|------|-------------|------|
| `duid` | string | Device UID | - |
| `lat` | float | Latitude | degrees |
| `long` | float | Longitude | degrees |
| `hr` | int | Heart Rate | bpm |
| `spo2` | int | Blood Oxygen | % |
| `amb_temp` | float | Ambient Temperature | °C |
| `obj_temp` | float | Object Temperature | °C |
| `ax` | float | Acceleration X | m/s² |
| `ay` | float | Acceleration Y | m/s² |
| `az` | float | Acceleration Z | m/s² |
| `motion` | boolean | Motion Detected | true/false |
| `light` | float | Light Level | lux |
| `batt_v` | float | Battery Voltage | V |
| `batt_pct` | int | Battery Percentage | % |

#### 4. Heartbeat (Liveness Check)
```json
{"heartbeat": true}
```

**Frequency:** Every 30 seconds (configurable)

**Purpose:** Keeps connection alive and indicates server is responding

**Usage:**
```javascript
ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.heartbeat) {
    console.log("💓 Server is alive at", new Date().toLocaleTimeString());
    // Reset heartbeat timeout
    clearTimeout(heartbeatTimeout);
    heartbeatTimeout = setTimeout(() => {
      console.warn("⚠️ No heartbeat for 60s, connection may be dead");
    }, 60000);
  }
};
```

#### 5. Error Messages
```json
{"error": "Device not found"}
```

**Possible Errors:**
- `"Device not found"` - Device UID doesn't exist in database
- Other Django/system errors

### Liveness Monitoring

**Method 1: Heartbeat Timeout**
```javascript
let lastHeartbeat = Date.now();
let heartbeatTimeout;

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);

  if (message.heartbeat) {
    lastHeartbeat = Date.now();
    
    // Reset watchdog
    clearTimeout(heartbeatTimeout);
    heartbeatTimeout = setTimeout(() => {
      console.warn("❌ No heartbeat received for 60 seconds");
      // Attempt reconnection
      reconnectWebSocket();
    }, 60000);
  }
};
```

**Method 2: Inactivity Detection**
```javascript
let lastMessageTime = Date.now();

ws.onmessage = (event) => {
  lastMessageTime = Date.now();
  const message = JSON.parse(event.data);
  
  // Handle message...
};

// Check connection every 10 seconds
setInterval(() => {
  const inactiveTime = Date.now() - lastMessageTime;
  
  if (inactiveTime > 90000) { // 90 seconds
    console.warn("Connection inactive, reconnecting...");
    ws.close();
    reconnectWebSocket();
  }
}, 10000);
```

**Method 3: Ping-Pong Pattern**
```javascript
// Client-side: Send ping every 25 seconds
setInterval(() => {
  if (ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({"ping": true}));
  }
}, 25000);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  if (message.pong) {
    console.log("✅ Server responded to ping");
  }
};
```

### Complete Example: Production Client

```javascript
class TelemetryClient {
  constructor(deviceId, deviceUid) {
    this.deviceId = deviceId;
    this.deviceUid = deviceUid;
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 3000;
    this.lastMessageTime = null;
  }

  connect() {
    const url = `ws://localhost/ws/telemetry/${this.deviceId}/`;
    console.log(`Connecting to ${url}`);
    
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      console.log("✅ WebSocket Connected");
      this.reconnectAttempts = 0;
      
      // Subscribe to device
      this.ws.send(JSON.stringify({
        "duid": this.deviceUid
      }));

      // Start liveness check
      this.startLivenessCheck();
    };

    this.ws.onmessage = (event) => {
      this.lastMessageTime = Date.now();
      const message = JSON.parse(event.data);

      if (message.telemetry) {
        this.onTelemetry(message.telemetry);
      } else if (message.heartbeat) {
        this.onHeartbeat();
      } else if (message.ok) {
        console.log("✅ Subscribed");
      } else if (message.error) {
        console.error("⚠️", message.error);
      }
    };

    this.ws.onerror = (error) => {
      console.error("❌ WebSocket Error:", error);
    };

    this.ws.onclose = () => {
      console.log("❌ WebSocket Closed");
      this.attemptReconnect();
    };
  }

  onTelemetry(data) {
    console.log("📊 Telemetry:", {
      device: data.duid,
      location: `${data.lat}, ${data.long}`,
      vitals: {
        heartRate: `${data.hr} bpm`,
        oxygen: `${data.spo2}%`,
        temperature: `${data.obj_temp}°C`
      },
      battery: `${data.batt_pct}%`
    });
  }

  onHeartbeat() {
    console.log(`💓 Alive at ${new Date().toLocaleTimeString()}`);
  }

  startLivenessCheck() {
    this.livenessCheckInterval = setInterval(() => {
      const timeSinceLastMessage = Date.now() - (this.lastMessageTime || Date.now());
      
      if (timeSinceLastMessage > 65000) { // 65 seconds
        console.warn("⚠️ Connection appears dead, reconnecting...");
        this.ws.close();
      }
    }, 10000);
  }

  attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * this.reconnectAttempts;
      console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
      
      setTimeout(() => {
        this.connect();
      }, delay);
    } else {
      console.error("Max reconnection attempts reached");
    }
  }

  disconnect() {
    if (this.livenessCheckInterval) {
      clearInterval(this.livenessCheckInterval);
    }
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Usage
const client = new TelemetryClient(2, "KTINO_002");
client.connect();
```

### Testing WebSocket in Browser Console

```javascript
// Quick test
const ws = new WebSocket("ws://localhost/ws/telemetry/2/");

ws.onopen = () => {
  console.log("Connected");
  ws.send(JSON.stringify({"duid": "KTINO_002"}));
};

ws.onmessage = (e) => {
  console.log("Message:", JSON.parse(e.data));
};

ws.onerror = (err) => {
  console.error("Error:", err);
};
```

### Debugging Tips

**Check WebSocket connection status:**
```javascript
console.log(ws.readyState);
// 0 = CONNECTING, 1 = OPEN, 2 = CLOSING, 3 = CLOSED
```

**Monitor all messages:**
```javascript
const originalSend = ws.send.bind(ws);
ws.send = function(data) {
  console.log("📤 Sending:", data);
  return originalSend(data);
};

const originalOnMessage = ws.onmessage;
ws.onmessage = function(event) {
  console.log("📥 Received:", event.data);
  return originalOnMessage.call(this, event);
};
```

**Browser DevTools:**
1. Open DevTools (F12)
2. Go to **Network** tab
3. Filter by **WS** (WebSocket)
4. Click on the WebSocket connection
5. Go to **Messages** tab to see all sent/received messages

### Generating Migrations

To generate migrations for your Django application, use the following Docker command:

```bash
docker-compose run --rm web python manage.py makemigrations
```

This will create migration files for any changes made to your models.

### Applying Migrations

To apply the migrations and update the database schema, run:

```bash
docker-compose run --rm web python manage.py migrate
```

### Running the Application

To start the application and all required services, use:

```bash
docker-compose up -d
```

This will start the Django application, MQTT broker, Redis, and other services in detached mode.

### Running All Services Together

To ensure all services are running and healthy, verify with:

```bash
docker-compose ps
```
