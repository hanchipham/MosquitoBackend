# IoT Larva Detection System - Backend

**Backend Service untuk Sistem Deteksi Jentik Nyamuk Berbasis ESP32-CAM**

Repository ini berisi source code backend yang dibangun menggunakan **FastAPI**. Sistem ini berfungsi menerima citra dari perangkat IoT, melakukan preprocessing, menjalankan inferensi AI (via Roboflow), serta mengelola logika kontrol (Decision Engine) untuk menjaga lingkungan bebas jentik.

## Fitur Utama

* **High-Performance API:** Dibangun di atas FastAPI dengan dukungan *asynchronous* untuk respon cepat.
* **Background Processing:** Proses inferensi AI dan update status dilakukan di *background* (`BackgroundTasks`), memungkinkan ESP32 segera kembali ke mode *Deep Sleep* setelah upload.
* **Secure Device Authentication:** Menggunakan HTTP Basic Auth dimana setiap device memiliki kredensial unik.
* **Smart Decision Engine:** Menggabungkan hasil deteksi AI dengan logika bisnis untuk menentukan status `AMAN` atau `BAHAYA`.
* **Manual & Auto Control:** Mendukung kontrol otomatis berdasarkan hasil deteksi, serta *manual override* via API untuk mengendalikan servo/pompa.
* **IoT Polling Mechanism:** Mekanisme polling efisien untuk sinkronisasi perintah antara server dan perangkat IoT.
* **Integrasi Pihak Ketiga:** Dukungan opsional untuk **Roboflow** (Inference) dan **Blynk** (Monitoring/Dashboard).
* **Automated Storage & DB:** Pembuatan struktur folder dan tabel database otomatis saat startup.

## 📂 Struktur Repositori

```text
MosquitoBackend/
├── app/
│   ├── api/                 # Definisi Endpoint (Routes)
│   ├── models/              # SQLAlchemy ORM Models (Device, Image, Inference, Alert)
│   ├── schemas/             # Pydantic Schemas (Request/Response Validation)
│   ├── services/            # Logic Layer (Roboflow, Blynk, Decision Engine, Device Control)
│   ├── utils/               # Utilities (Image processing, helpers)
│   ├── auth.py              # Autentikasi HTTP Basic
│   ├── config.py            # Manajemen konfigurasi (.env)
│   └── database.py          # Konfigurasi Database Session
├── storage/                 # Penyimpanan gambar (Auto-generated)
│   ├── original/
│   └── preprocessed/
├── main.py                  # Entry point aplikasi
├── register_device.py       # Script utilitas untuk pendaftaran device
├── requirements.txt         # Daftar dependensi Python
├── .env.example             # Template variabel lingkungan
└── README.md                # Dokumentasi proyek

```

## Panduan Instalasi (Quick Start)

### 1. Persiapan Lingkungan

Pastikan Python 3.9+ dan MySQL server telah terinstall.

```bash
# Clone repository (jika belum)
git clone https://github.com/username/MosquitoBackend.git
cd MosquitoBackend

# Buat virtual environment (Disarankan)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# atau
venv\Scripts\activate     # Windows

# Install dependensi
pip install -r requirements.txt

```

### 2. Konfigurasi Database & Environment

Salin file contoh konfigurasi:

```bash
cp .env.example .env

```

Sesuaikan variabel di dalam `.env` dengan kredensial Anda:

| Variabel | Deskripsi | Wajib? |
| --- | --- | --- |
| `DATABASE_URL` | Koneksi MySQL (`mysql+pymysql://user:pass@host/db`) | **Ya** |
| `SECRET_KEY` | Kunci acak untuk keamanan internal | **Ya** |
| `ROBOFLOW_API_KEY` | API Key Roboflow untuk inferensi | Opsional* |
| `ROBOFLOW_WORKFLOW_ID` | ID Workflow Roboflow | Opsional* |
| `BLYNK_AUTH_TOKEN` | Token Auth Blynk untuk notifikasi | Opsional |
| `TIMEZONE` | Zona waktu server (misal: `Asia/Jakarta`) | Tidak |

*> Catatan: Jika Roboflow tidak dikonfigurasi, sistem tetap berjalan namun status inferensi akan gagal.*

### 3. Registrasi Perangkat (Device Onboarding)

Sebelum ESP32 dapat mengirim data, perangkat harus didaftarkan ke sistem untuk mendapatkan kredensial.

Jalankan script interaktif:

```bash
python register_device.py

```

Atau via command line arguments:

```bash
# Usage: python register_device.py [CODE] [PASSWORD] [LOCATION] [DESCRIPTION]
python register_device.py ESP32_CAM_01 securePass123 "Toren Belakang" "Monitoring Toren Utama"

```

### 4. Menjalankan Server

```bash
# Mode development dengan auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Atau menggunakan python wrapper
python main.py

```

Aplikasi akan berjalan di `http://localhost:8000`. Dokumentasi interaktif tersedia di `/docs`.

---

## API Reference

Semua endpoint (kecuali `/health`) memerlukan header:
`Authorization: Basic <base64(device_code:password)>`

### 1. Core Functionality

#### `POST /api/upload`

Menerima gambar dari ESP32.

* **Flow:** Simpan gambar → Response `SLEEP` ke ESP32 → Trigger Background Inference.
* **Body:** `multipart/form-data` (`image`, `captured_at`).
* **Response:**

```json
{
  "success": true,
  "action": "SLEEP",
  "status": "PROCESSING",
  "message": "Image uploaded, processing in background"
}

```

#### `GET /api/device/{device_code}/control`

Endpoint polling untuk IoT. Mengecek apakah ada perintah manual atau aksi otomatis yang harus dijalankan.

* **Response:**
* `mode`: `MANUAL` atau `AUTO`.
* `command`: `ACTIVATE_SERVO`, `STOP_SERVO`, atau `NO_OP`.

#### `POST /api/device/{device_code}/control/executed`

Callback dari IoT untuk memberitahu server bahwa perintah fisik telah berhasil dilakukan.

### 2. Manual Control (User Dashboard)

* **`POST /api/device/{device_code}/activate_servo`**: Memaksa servo aktif (Manual Override).
* **`POST /api/device/{device_code}/stop_servo`**: Memaksa servo berhenti.
* **`GET /api/device/{device_code}/control/status`**: Melihat status kontrol terakhir.

### 3. Utility

* **`GET /api/device/info`**: Mendapatkan metadata device yang sedang login.
* **`GET /api/health`**: Cek status server (Tanpa Auth).

---

## Alur Kerja Sistem (System Flow)

1. **Capture & Upload:** ESP32 mengambil foto dan mengirim ke `/api/upload`.
2. **Immediate Response:** Server menyimpan gambar original & preprocessed, lalu **segera** merespon dengan `action: SLEEP` agar hemat daya.
3. **Background Task:**

* Server mengirim gambar ke Roboflow.
* Hasil inferensi (jumlah jentik) disimpan ke database.
* **Decision Engine** mengevaluasi hasil:
* Jika `jentik > 0`: Set status `BAHAYA`, buat Alert, siapkan command `ACTIVATE_SERVO` (jika mode Auto).
* Jika `jentik == 0`: Set status `AMAN`, resolve Alert, siapkan command `STOP_SERVO`.

* Update status ke Blynk (jika dikonfigurasi).

1. **Action Execution:**

* Pada siklus bangun berikutnya, ESP32 memanggil `/control`.
* Server memberikan perintah tertunda (hasil decision engine atau manual override).
* ESP32 mengeksekusi perintah dan melapor balik ke `/control/executed`.

---

## 🛠 Testing & Development

Repository ini menyertakan script untuk pengujian tanpa perangkat fisik:

* `test_upload.py`: Mengirim file gambar dummy untuk menguji endpoint upload dan background processing.
* `test_manual_control.py`: Simulasi alur kontrol manual (User request -> Pending -> IoT Polling -> Executed).

Untuk testing API secara visual, gunakan **Swagger UI** di `http://localhost:8000/docs`.

## Model Data

Sistem menggunakan tabel berikut (dibuat otomatis):

* `devices`: Registry perangkat.
* `device_auth`: Kredensial keamanan.
* `images`: Metadata file gambar.
* `inference_results`: Raw JSON dari Roboflow & statistik deteksi.
* `alerts`: Log peringatan bahaya.
* `device_controls`: State manajemen untuk perintah servo.
