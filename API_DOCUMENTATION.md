# API Documentation - Mosquito Detection Backend

## Base URL

```markdown
http://localhost:8080
```

## Authentication

Semua endpoint (kecuali `/health`) menggunakan **HTTP Basic Authentication** dengan device credentials.

### Format Authentication

```markdown
Authorization: Basic base64(device_code:password)
```

---

## Endpoints

### 1. Upload Image (ESP32 Endpoint)

**Endpoint:** `POST /api/upload`

**Description:** Upload gambar dari ESP32 untuk deteksi jentik nyamuk. Sistem akan:

1. Menyimpan gambar original
2. Preprocessing gambar
3. Response cepat ke ESP32 (action: ACTIVATE/SLEEP)
4. Inference di background dengan Roboflow
5. Update Blynk (jika configured)

**Authentication:** Required (HTTP Basic Auth)

**Request:**

- **Method:** POST
- **Content-Type:** multipart/form-data
- **Headers:**

  ```markdown
  Authorization: Basic <base64_credentials>
  ```

- **Body:**

  ```markdown
  image: file (binary)
  captured_at: string (optional, ISO format datetime)
  ```

**Response Success (200):**

```json
{
  "status": "success",
  "message": "Image uploaded successfully",
  "action": "SLEEP",
  "image_id": "243074ea-ce6c-4c68-9b36-2818c23fbe86",
  "device_code": "test",
  "timestamp": "2026-01-02T04:22:24.123456+07:00"
}
```

**Response Fields:**

- `status`: "success" | "error"
- `message`: Informasi hasil upload
- `action`: "ACTIVATE" (ada jentik) | "SLEEP" (aman)
- `image_id`: UUID gambar yang tersimpan
- `device_code`: Kode device yang upload
- `timestamp`: Waktu upload (timezone dari config)

**Response Error (401):**

```json
{
  "detail": "Invalid credentials"
}
```

**Response Error (500):**

```json
{
  "status": "error",
  "message": "Error description",
  "action": "SLEEP"
}
```

#### Contoh Penggunaan

**cURL:**

```bash
curl -X POST http://localhost:8080/api/upload \
  -u "ESP32_TEST_01:password123" \
  -F "image=@/path/to/image.jpg" \
  -F "captured_at=2026-01-02T10:30:00Z"
```

**Python:**

```python
import requests
from requests.auth import HTTPBasicAuth

url = "http://localhost:8080/api/upload"
auth = HTTPBasicAuth("ESP32_TEST_01", "password123")

with open("image.jpg", "rb") as f:
    files = {"image": f}
    data = {"captured_at": "2026-01-02T10:30:00Z"}
    response = requests.post(url, auth=auth, files=files, data=data)
    
print(response.json())
```

**ESP32 (Arduino):**

```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <base64.h>

const char* serverUrl = "http://192.168.1.100:8080/api/upload";
const char* deviceCode = "ESP32_TEST_01";
const char* password = "password123";

void uploadImage(uint8_t* imageData, size_t imageSize) {
    HTTPClient http;
    http.begin(serverUrl);
    
    // Basic Auth
    String auth = String(deviceCode) + ":" + String(password);
    String authEncoded = base64::encode(auth);
    http.addHeader("Authorization", "Basic " + authEncoded);
    
    // Multipart form data
    String boundary = "----ESP32Boundary";
    http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);
    
    String body = "--" + boundary + "\r\n";
    body += "Content-Disposition: form-data; name=\"image\"; filename=\"image.jpg\"\r\n";
    body += "Content-Type: image/jpeg\r\n\r\n";
    
    // Send request
    int httpCode = http.POST(imageData, imageSize);
    
    if (httpCode > 0) {
        String response = http.getString();
        Serial.println(response);
        
        // Parse JSON dan ambil action
        // if (action == "ACTIVATE") { jalankan pompa }
        // else { sleep mode }
    }
    
    http.end();
}
```

---

### 2. Get Device Info

**Endpoint:** `GET /api/device/info`

**Description:** Mendapatkan informasi detail device yang sedang login

**Authentication:** Required (HTTP Basic Auth)

**Request:**

- **Method:** GET
- **Headers:**

  ```markdown
  Authorization: Basic <base64_credentials>
  ```

**Response Success (200):**

```json
{
  "id": "4ebc0405-7647-436a-a448-4ac8f0a462cb",
  "device_code": "ESP32_TEST_01",
  "location": "Kantor Depan",
  "description": "Testing device",
  "is_active": true,
  "created_at": "2026-01-01T15:30:00+07:00"
}
```

**Response Error (401):**

```json
{
  "detail": "Invalid credentials"
}
```

#### Contoh Penggunaan

**cURL:**

```bash
curl -X GET http://localhost:8080/api/device/info \
  -u "ESP32_TEST_01:password123"
```

**Python:**

```python
import requests
from requests.auth import HTTPBasicAuth

url = "http://localhost:8080/api/device/info"
auth = HTTPBasicAuth("ESP32_TEST_01", "password123")

response = requests.get(url, auth=auth)
print(response.json())
```

---

### 3. Health Check

**Endpoint:** `GET /api/health`

**Description:** Cek status server

**Authentication:** None

**Request:**

- **Method:** GET

**Response Success (200):**

```json
{
  "status": "healthy",
  "timestamp": "2026-01-02T12:00:00+07:00"
}
```

#### Contoh Penggunaan

**cURL:**

```bash
curl http://localhost:8080/api/health
```

**Python:**

```python
import requests

response = requests.get("http://localhost:8080/api/health")
print(response.json())
```

---

## Flow Diagram

```markdown
ESP32 Capture Image
    ↓
POST /api/upload (with auth)
    ↓
Backend: Save Original Image
    ↓
Backend: Preprocess Image
    ↓
Backend: Response cepat (ACTIVATE/SLEEP) ← ESP32 terima response
    ↓
[Background Process]
    ↓
Roboflow Workflow Inference
    ↓
Parse Predictions (count jentik)
    ↓
Decision Engine (AMAN/BAHAYA)
    ↓
Update Blynk Dashboard
    ↓
Create/Resolve Alerts in Database
```

---

## Database Schema

### Images Table

Menyimpan gambar original dan preprocessed

```sql
- id (UUID)
- device_id (UUID, FK)
- device_code (string)
- image_type (original | preprocessed)
- image_path (string)
- width, height (int)
- checksum (string)
- captured_at (datetime)
- uploaded_at (datetime)
```

### Inference Results Table

Menyimpan hasil inference dari Roboflow

```sql
- id (UUID)
- image_id (UUID, FK)
- device_id (UUID, FK)
- device_code (string)
- inference_at (datetime)
- raw_prediction (JSON) - Full response dari Roboflow
- total_objects (int)
- total_jentik (int)
- total_non_jentik (int)
- avg_confidence (float)
- parsing_version (string)
- status (success | failed)
- error_message (text)
```

### Alerts Table

Menyimpan alert status BAHAYA

```sql
- id (UUID)
- device_id (UUID, FK)
- device_code (string)
- alert_type (BAHAYA)
- alert_message (text)
- alert_level (info | warning | critical)
- created_at (datetime)
- resolved_at (datetime, nullable)
```

---

## Environment Variables

File `.env` configuration:

```env
# Database
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/mosquito_db

# Roboflow (Workflow Mode)
ROBOFLOW_API_KEY=your_api_key
ROBOFLOW_WORKSPACE=your_workspace
ROBOFLOW_WORKFLOW_ID=workflow_id

# Blynk (Optional)
BLYNK_AUTH_TOKEN=your_blynk_token
BLYNK_TEMPLATE_ID=your_template_id

# Timezone (WIB/UTC/etc)
TIMEZONE=Asia/Jakarta

# Security
SECRET_KEY=your_secret_key
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (invalid parameters) |
| 401 | Unauthorized (invalid credentials) |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## Rate Limiting

Belum diimplementasi (untuk production sebaiknya tambahkan rate limiting)

---

## Testing

### Register Device Baru

```bash
python register_device.py
# Atau langsung via script:
python register_device.py ESP32_TEST_01 password123 "Kantor Depan" "Testing device"
```

### Test Upload via Script

```bash
python test_upload.py
```

### Test via Swagger UI

Buka browser: `http://localhost:8080/docs`

### Test via Postman

1. Import collection dari `/docs` atau buat manual
2. Setup Authorization → Basic Auth
3. Test endpoint `/api/upload` dengan sample image

---

## Production Deployment

### Railway/Heroku

1. Set environment variables di dashboard
2. Set `DATABASE_URL` ke MySQL production
3. Set `TIMEZONE` sesuai region
4. Deploy via Git push

### Docker

```bash
docker build -t mosquito-backend .
docker run -p 8080:8080 --env-file .env mosquito-backend
```

### Security Checklist

- ✅ HTTPS only in production
- ✅ Strong SECRET_KEY
- ✅ Database password yang kuat
- ✅ Rate limiting untuk production
- ✅ CORS configuration jika ada frontend
- ⚠️ Backup database regular

---

## Support & Contact

Untuk pertanyaan atau issue, silakan buka issue di repository atau contact developer.

---
