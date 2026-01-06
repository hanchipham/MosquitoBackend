# IoT Larva Detection System - Backend

Backend FastAPI untuk sistem deteksi jentik nyamuk menggunakan ESP32-CAM.

## Struktur Project

```
MosquitoBackend/
├── app/
│   ├── api/
│   │   └── endpoints.py          # API endpoints
│   ├── models/
│   │   ├── device.py             # Device & DeviceAuth models
│   │   ├── image.py              # Image model
│   │   ├── inference.py          # InferenceResult model
│   │   └── alert.py              # Alert model
│   ├── schemas/
│   │   └── schemas.py            # Pydantic schemas
│   ├── services/
│   │   ├── roboflow_service.py   # Roboflow integration
│   │   ├── blynk_service.py      # Blynk integration
│   │   └── decision_engine.py    # Decision logic
│   ├── utils/
│   │   └── image_utils.py        # Image processing utilities
│   ├── auth.py                   # Authentication
│   ├── config.py                 # Configuration
│   └── database.py               # Database setup
├── storage/                       # Image storage (auto-created)
├── main.py                        # FastAPI application
├── register_device.py             # Script registrasi device
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
└── README.md                      # Dokumentasi
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Setup Environment Variables

Copy `.env.example` ke `.env` dan isi dengan konfigurasi Anda:

```bash
cp .env.example .env
```

Edit `.env`:

- `DATABASE_URL`: Connection string MySQL Anda
- `ROBOFLOW_API_KEY`: API key dari Roboflow
- `ROBOFLOW_MODEL_ID`: Model ID dari Roboflow
- `BLYNK_AUTH_TOKEN`: Auth token dari Blynk
- `SECRET_KEY`: Secret key untuk security

### 3. Setup Database

Pastikan MySQL sudah running dan database sudah dibuat:

```sql
CREATE DATABASE mosquito_db;
```

Database tables akan otomatis dibuat saat aplikasi pertama kali dijalankan.

### 4. Register Device

Sebelum ESP32 bisa upload, device harus didaftarkan terlebih dahulu:

```bash
python register_device.py ESP32_TOREN_01 password123 "Toren Depan" "ESP32-CAM di toren depan"
```

Atau jalankan interactive mode:

```bash
python register_device.py
```

Simpan credentials (device_code dan password) untuk dikonfigurasi di ESP32.

### 5. Run Server

```bash
python main.py
```

Atau dengan uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server akan berjalan di `http://localhost:8000`

## API Endpoints

### 1. Upload Image (ESP32)

**Endpoint:** `POST /api/upload`

**Authentication:** HTTP Basic Auth

- Username: `device_code`
- Password: `device_password`

**Request:**

- `image`: File (multipart/form-data)
- `captured_at`: String (ISO datetime, optional)

**Response:**

```json
{
  "success": true,
  "message": "Image uploaded successfully, processing in background",
  "action": "SLEEP",
  "status": "PROCESSING",
  "device_code": "ESP32_TOREN_01",
  "total_jentik": 0,
  "total_objects": 0
}
```

Action yang mungkin:

- `ACTIVATE`: ESP32 harus mengaktifkan servo/pompa
- `SLEEP`: ESP32 masuk deep sleep

### 2. Device Info

**Endpoint:** `GET /api/device/info`

**Authentication:** HTTP Basic Auth

**Response:**

```json
{
  "id": "uuid",
  "device_code": "ESP32_TOREN_01",
  "location": "Toren Depan",
  "description": "ESP32-CAM di toren depan",
  "is_active": true,
  "created_at": "2025-01-02T10:00:00"
}
```

### 3. Health Check

**Endpoint:** `GET /api/health`

**Authentication:** None

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2025-01-02T10:00:00"
}
```

## Flow Sistem

Sesuai dengan `rancangan.md`:

1. **ESP32** capture image dan upload ke `/api/upload`
2. **Backend** menerima, authenticate device
3. **Backend** save original image ke filesystem
4. **Backend** save image metadata ke database
5. **Backend** preprocessing image (resize, enhance)
6. **Backend** response cepat ke ESP32 (action: SLEEP)
7. **Backend** (background) kirim image ke Roboflow
8. **Backend** (background) parse hasil inference
9. **Backend** (background) simpan hasil ke database
10. **Backend** (background) decision engine (AMAN/BAHAYA)
11. **Backend** (background) handle alerts
12. **Backend** (background) update Blynk dashboard
13. **ESP32** terima response, execute action

## Testing dengan Postman

### Setup Basic Auth

1. Di Postman, pilih tab **Authorization**
2. Type: **Basic Auth**
3. Username: `ESP32_TOREN_01` (device_code Anda)
4. Password: `password123` (password device Anda)

### Upload Image

1. Method: **POST**
2. URL: `http://localhost:8000/api/upload`
3. Body: **form-data**
   - Key: `image`, Type: **File**, Value: pilih file image
   - Key: `captured_at`, Type: **Text**, Value: `2025-01-02T10:00:00` (optional)
4. Send

## Database Schema

Sesuai dengan `rancangan.md`:

- **devices**: Device registry
- **device_auth**: Device credentials
- **images**: Image storage metadata
- **inference_results**: Hasil inference dari Roboflow
- **alerts**: Alert notifications

## Development Notes

### Background Processing

Inference dijalankan sebagai background task agar:

- ESP32 tidak perlu menunggu lama
- Response cepat diterima
- Sistem tetap responsive meski ada 10+ device concurrent

### Error Handling

Jika Roboflow error:

- Image tetap disimpan
- Inference result status = `failed`
- Error message disimpan ke database
- Blynk status = "INFERENCE ERROR"
- ESP32 default action = SLEEP

### Alert Logic

Alert dibuat hanya jika:

- `total_jentik > 0`
- Belum ada alert yang belum resolved

Alert di-resolve otomatis saat `total_jentik == 0`
