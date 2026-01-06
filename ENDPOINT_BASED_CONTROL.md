# Endpoint-Based Servo Control API

## Design Philosophy

**The endpoint IS the command** - No control_command or status fields needed!

Binary servo control with explicit endpoints:

- Call endpoint = execute command
- Minimal IoT logic: `call endpoint → execute → done`

## API Endpoints

### Control Commands (Admin/API)

#### Activate Servo

```
POST /api/device/{device_code}/activate_servo
```

**The endpoint itself activates the servo** - no command field needed!

**Request:**

- Auth: HTTP Basic (device_code:password)
- Body (optional): `message` (form-data)

**Response:**

```json
{
  "success": true,
  "device_code": "test",
  "command": "ACTIVATE_SERVO",
  "status": "PENDING",
  "message": "Servo activation requested",
  "timestamp": "2026-01-06T15:21:51"
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8080/api/device/test/activate_servo \
  -u test:123 \
  -F "message=Activating servo now"
```

---

#### Stop Servo

```
POST /api/device/{device_code}/stop_servo
```

**The endpoint itself stops the servo** - no command field needed!

**Request:**

- Auth: HTTP Basic (device_code:password)
- Body (optional): `message` (form-data)

**Response:**

```json
{
  "success": true,
  "device_code": "test",
  "command": "STOP_SERVO",
  "status": "PENDING",
  "message": "Servo stop requested",
  "timestamp": "2026-01-06T15:22:10"
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8080/api/device/test/stop_servo \
  -u test:123 \
  -F "message=Stopping servo"
```

---

### Status Updates (IoT Device)

#### Mark as Executed

```
POST /api/device/{device_code}/control/executed
```

**The endpoint itself marks status as EXECUTED** - no status field needed!

**Request:**

- Auth: HTTP Basic (device_code:password)
- Body (optional): `message` (form-data)

**Response:**

```json
{
  "success": true,
  "device_code": "test",
  "command": "ACTIVATE_SERVO",
  "status": "EXECUTED",
  "message": "Servo activated successfully",
  "timestamp": "2026-01-06T15:21:58"
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8080/api/device/test/control/executed \
  -u test:123 \
  -F "message=Servo activated successfully"
```

---

#### Mark as Failed

```
POST /api/device/{device_code}/control/failed
```

**The endpoint itself marks status as FAILED** - no status field needed!

**Request:**

- Auth: HTTP Basic (device_code:password)
- Body (optional): `message` (form-data)

**Response:**

```json
{
  "success": true,
  "device_code": "test",
  "command": "ACTIVATE_SERVO",
  "status": "FAILED",
  "message": "Servo timeout error",
  "timestamp": "2026-01-06T15:22:30"
}
```

**cURL Example:**

```bash
curl -X POST http://localhost:8080/api/device/test/control/failed \
  -u test:123 \
  -F "message=Servo timeout error"
```

---

### Poll & Status (IoT Device)

#### Poll for Control

```
GET /api/device/{device_code}/control
```

IoT polls this endpoint to get current control command.

**Response (Manual Override):**

```json
{
  "mode": "MANUAL",
  "command": "ACTIVATE_SERVO",
  "status": "PENDING",
  "message": "Admin activated servo",
  "timestamp": "2026-01-06T15:21:51"
}
```

**Response (Automatic Mode):**

```json
{
  "mode": "AUTO",
  "command": "STOP_SERVO",
  "status": "AUTO",
  "message": "Automatic control based on inference",
  "timestamp": "2026-01-06T15:22:00"
}
```

---

#### Get Control Status

```
GET /api/device/{device_code}/control/status
```

Get current control configuration.

**Response:**

```json
{
  "device_code": "test",
  "command": "ACTIVATE_SERVO",
  "status": "EXECUTED",
  "message": "Servo activated successfully",
  "created_at": "2026-01-06T13:09:46",
  "updated_at": "2026-01-06T15:21:58"
}
```

---

## IoT Integration Flow

### Complete Flow Example

```
1. ADMIN: POST /activate_servo
   └─> System sets control_command=ACTIVATE_SERVO, status=PENDING

2. IoT: GET /control
   └─> Response: mode=MANUAL, command=ACTIVATE_SERVO, status=PENDING
   
3. IoT: Execute servo activation
   
4. IoT: POST /control/executed
   └─> System updates status=EXECUTED
```

### ESP32 Example Code

```cpp
#include <HTTPClient.h>
#include <base64.h>

const char* deviceCode = "test";
const char* password = "123";
const char* serverUrl = "http://your-server.com/api/device";

String getBasicAuth() {
  String auth = String(deviceCode) + ":" + String(password);
  return "Basic " + base64::encode(auth);
}

void pollControl() {
  HTTPClient http;
  http.begin(String(serverUrl) + "/" + deviceCode + "/control");
  http.addHeader("Authorization", getBasicAuth());
  
  int httpCode = http.GET();
  if (httpCode == 200) {
    String payload = http.getString();
    // Parse JSON
    if (mode == "MANUAL" && status == "PENDING") {
      if (command == "ACTIVATE_SERVO") {
        activateServo();
        markExecuted("Servo activated");
      } else if (command == "STOP_SERVO") {
        stopServo();
        markExecuted("Servo stopped");
      }
    }
  }
  http.end();
}

void markExecuted(String msg) {
  HTTPClient http;
  http.begin(String(serverUrl) + "/" + deviceCode + "/control/executed");
  http.addHeader("Authorization", getBasicAuth());
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");
  
  String postData = "message=" + msg;
  http.POST(postData);
  http.end();
}

void markFailed(String error) {
  HTTPClient http;
  http.begin(String(serverUrl) + "/" + deviceCode + "/control/failed");
  http.addHeader("Authorization", getBasicAuth());
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");
  
  String postData = "message=" + error;
  http.POST(postData);
  http.end();
}
```

---

## Key Benefits

**Minimal IoT Logic**

- No need to construct command payloads
- Just call the endpoint - that's the command!

**Binary Control**

- Only two actions: activate_servo / stop_servo
- No complex modes or parameters

**Explicit & Clear**

- Endpoint name = exact action
- No ambiguity about what happens

**Simple Status Updates**

- Call /executed = mark as executed
- Call /failed = mark as failed
- No need to specify status in body

**HTTP-Native Design**

- RESTful endpoints
- Uses HTTP verbs correctly (POST for actions)
- Standard auth (Basic Auth)

---

## Comparison: Old vs New

| Aspect | Old Design | New Design |
|--------|-----------|-----------|
| **Set Command** | POST /control/set + command field | POST /activate_servo |
| **Update Status** | POST /control/update + status field | POST /control/executed |
| **Command Source** | Request body field | Endpoint itself |
| **Status Source** | Request body field | Endpoint itself |
| **IoT Complexity** | Parse body, set fields | Just call endpoint |
| **Payload Size** | Larger (command/status fields) | Minimal (optional message) |

---

## Testing

Run the test script:

```bash
python test_manual_control.py
```

Default credentials:

- Device Code: `test`
- Password: `123`

Interactive menu options:

1. POST /activate_servo
2. POST /stop_servo  
3. GET /control (poll)
4. POST /control/executed
5. POST /control/failed
6. GET /control/status
7. Simulate complete flow
8. Run full test suite

---

## Security

- HTTP Basic Authentication required
- Device can only control itself (verified in auth)
- Use HTTPS in production
- Passwords hashed with bcrypt in database

---

## Database Schema

Table: `device_controls`

| Field | Type | Description |
|-------|------|-------------|
| id | CHAR(36) | UUID primary key |
| device_id | CHAR(36) | FK to devices (unique) |
| device_code | VARCHAR(100) | Device code (unique) |
| control_command | VARCHAR(50) | ACTIVATE_SERVO / STOP_SERVO |
| status | VARCHAR(20) | PENDING / EXECUTED / FAILED |
| message | TEXT | Optional message |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |

**One control per device** (upsert pattern on device_code)
