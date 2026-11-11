# Cara Menjalankan Aplikasi Chatbot Tematik

Panduan ini ditulis untuk pemula. Ikuti dari atas ke bawah; setiap perintah bisa disalin langsung.

## Daftar isi

1. [Persiapan sekali saja](#1-persiapan-sekali-saja)
2. [Menjalankan setiap tahap](#2-menjalankan-setiap-tahap)
3. [Menjalankan aplikasi final](#3-menjalankan-aplikasi-final)
4. [Chat di terminal](#4-chat-di-terminal)
5. [Menjalankan uji otomatis](#5-menjalankan-uji-otomatis)
6. [Mengukur akurasi chatbot](#6-mengukur-akurasi-chatbot)
7. [Menambah tema sendiri](#7-menambah-tema-sendiri)
8. [Pengaturan lewat variabel lingkungan](#8-pengaturan-lewat-variabel-lingkungan)
9. [Menghentikan server](#9-menghentikan-server)
10. [Masalah yang sering terjadi](#10-masalah-yang-sering-terjadi)

---

## 1. Persiapan sekali saja

### 1.1 Pasang Python 3.10 atau lebih baru

- **Windows**: unduh dari https://www.python.org/downloads/ lalu jalankan installer.
  **Centang "Add python.exe to PATH"** sebelum klik *Install Now*.
- **macOS**: `brew install python` atau unduh installer dari python.org.
- **Linux (Ubuntu/Debian)**: `sudo apt install python3 python3-venv python3-pip`

Periksa di terminal (Command Prompt / PowerShell / Terminal):

```bash
python --version        # Windows
python3 --version       # macOS / Linux
```

Harus muncul `Python 3.10` atau lebih tinggi.

> Di macOS/Linux, ganti setiap `python` di panduan ini dengan `python3` bila `python` tidak dikenal.

### 1.2 Ekstrak paket dan buka foldernya

Ekstrak `chatbot-tematik-flask.zip`, lalu buka terminal di folder hasil ekstrak:

```bash
cd lokasi/anda/chatbot-tematik-flask
```

Tip: di VS Code pilih **File › Open Folder…**, lalu buka terminal dengan **Ctrl + `**.

### 1.3 Buat dan aktifkan virtual environment

Virtual environment (venv) adalah "ruang" khusus agar pustaka proyek tidak bercampur dengan sistem.
Cukup **satu venv di folder utama** untuk semua tahap.

```bash
python -m venv venv
```

Aktifkan:

| Sistem | Perintah |
| --- | --- |
| Windows (Command Prompt) | `venv\Scripts\activate` |
| Windows (PowerShell) | `venv\Scripts\Activate.ps1` |
| macOS / Linux | `source venv/bin/activate` |

Jika berhasil, awal baris terminal berubah menjadi `(venv)`.
**Aktifkan venv setiap kali membuka terminal baru.**

> PowerShell menolak menjalankan skrip? Jalankan sekali:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, lalu coba lagi.

### 1.4 Pasang pustaka

```bash
pip install -r requirements.txt
```

Periksa: `flask --version` harus menampilkan Flask 3.x.

---

## 2. Menjalankan setiap tahap

Setiap tahap berdiri sendiri. Masuk ke foldernya, jalankan, lalu buka alamat yang tertulis.
Hentikan server dengan **Ctrl + C** sebelum pindah ke tahap berikutnya.

### Tahap 1 — Halo, Flask

```bash
cd tahapan/tahap-01-halo-flask
python app.py
```

Buka di browser:

| Alamat | Yang terlihat |
| --- | --- |
| http://127.0.0.1:5000/ | Halo, Flask! |
| http://127.0.0.1:5000/halo/Budi | Halo, Budi! (variabel URL) |
| http://127.0.0.1:5000/cari?q=krs | Anda mencari: krs (query string) |
| http://127.0.0.1:5000/cari | Pesan galat dengan kode 400 |
| http://127.0.0.1:5000/api/info | Data JSON berisi waktu server |

### Tahap 2 — Template dan form ("bot beo")

```bash
cd ../tahap-02-template-dan-form
python app.py
```

Buka http://127.0.0.1:5000, klik **Coba bot beo**, lalu kirim pesan. Perhatikan:
setiap pesan membuat **seluruh halaman dimuat ulang**. Ini diperbaiki di Tahap 5.

### Tahap 3 — Chatbot di terminal

Tidak ada server web di tahap ini.

```bash
cd ../tahap-03-chatbot-terminal
python bandingkan.py          # bandingkan mesin v1 (kata kunci) dan v2 (kemiripan)
python cli.py                 # chat dengan mesin v2
python cli.py --versi 1       # chat dengan mesin v1
python cli.py --debug         # tampilkan 3 kandidat intent dan skornya
```

Ketik `keluar` untuk berhenti. Hasil `bandingkan.py` yang diharapkan: **versi 1 = 6/9, versi 2 = 9/9**.

### Tahap 4 — REST API

Butuh **dua terminal** (keduanya dengan venv aktif).

Terminal 1:

```bash
cd tahapan/tahap-04-api-json
python app.py
```

Terminal 2:

```bash
cd tahapan/tahap-04-api-json
python uji_api.py
```

Hasil yang diharapkan: empat request; tiga dijawab `200`, satu (pesan kosong) dijawab `400`.

Alternatif dengan curl:

```bash
# Linux / macOS / Git Bash
curl -X POST http://127.0.0.1:5000/api/chat -H "Content-Type: application/json" -d '{"message": "cara bayar ukt"}'
```

```powershell
# Windows PowerShell
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/chat -Method Post -ContentType "application/json" -Body '{"message": "cara bayar ukt"}'
```

### Tahap 5 — Antarmuka chat

```bash
cd tahapan/tahap-05-antarmuka-chat
python app.py
```

Buka http://127.0.0.1:5000. Pesan terkirim **tanpa memuat ulang halaman**.
Tekan **F12 › tab Network** untuk melihat request `POST /api/chat`.

---

## 3. Menjalankan aplikasi final

```bash
cd aplikasi-final
python app.py
```

| Alamat | Isi |
| --- | --- |
| http://127.0.0.1:5000/ | Pilih tema: Kampus, Kuliner, atau Wisata |
| http://127.0.0.1:5000/chat/kampus | Chat dengan SiAkad |
| http://127.0.0.1:5000/admin/kampus | Statistik dan daftar pertanyaan yang tidak dikenali |

Fitur yang bisa dicoba:

- Centang **Mode belajar** di halaman chat untuk melihat 3 kandidat intent beserta skornya.
- Muat ulang halaman (F5): riwayat tetap tampil karena disimpan di `chat_history.db`.
- Klik **Hapus riwayat** untuk mengosongkan percakapan sesi Anda.
- Klik **Statistik** untuk membuka halaman admin tema tersebut.

File database `chat_history.db` dibuat otomatis. Hapus file ini bila ingin memulai dari nol.

---

## 4. Chat di terminal

Dari folder `aplikasi-final`:

```bash
python cli.py                     # tema kampus
python cli.py --tema kuliner      # tema lain
python cli.py --debug             # tampilkan kandidat intent
python cli.py --ambang 0.6        # coba ambang batas lain
```

---

## 5. Menjalankan uji otomatis

Dari folder `aplikasi-final`:

```bash
pytest -v
```

Hasil yang diharapkan pada baris terakhir: **`34 passed`**.
Uji memakai database sementara, sehingga tidak mengubah `chat_history.db`.

Menjalankan sebagian uji saja:

```bash
pytest tests/test_engine.py -v          # hanya mesin chatbot
pytest -k admin -v                      # hanya uji yang namanya memuat "admin"
```

---

## 6. Mengukur akurasi chatbot

`evaluate.py` menguji bot dengan kalimat di `evaluasi/<tema>.csv` yang **tidak** ada di file tema.

```bash
python evaluate.py --tema kampus            # akurasi, per intent, dan daftar kesalahan
python evaluate.py --tema kampus --sweep    # bandingkan beberapa ambang batas
```

Hasil saat paket ini dibuat:

| Tema | Kalimat uji | Akurasi (ambang 0,45) |
| --- | --- | --- |
| kampus | 29 | 93,1% |
| kuliner | 11 | 100% |
| wisata | 10 | 90,0% |

Kesalahan di tema kampus ("uang kuliah tunggal dibayar kemana", "tempat baca buku kampus buka kapan")
sengaja dibiarkan: keduanya memakai sinonim yang tidak ada di pola. Inilah batas pendekatan berbasis aturan.

---

## 7. Menambah tema sendiri

1. Salin `template-tema.json` ke `aplikasi-final/themes/`, misalnya menjadi `themes/perpus.json`.
2. Ubah `id` menjadi `"perpus"` (sama dengan nama file), lalu isi `name`, `bot_name`, `color`, dan seterusnya.
3. Tambahkan minimal 10 intent; setiap intent minimal 5 pola dan 2 respons.
4. Jalankan ulang `python app.py`. Tema baru muncul otomatis di halaman utama.
5. Bila file tema salah, aplikasi berhenti dengan pesan yang menyebut masalahnya, misalnya
   `pola 'halo' ada di intent 'salam' dan 'sapa'`.
6. Buat `evaluasi/perpus.csv` (kolom `kalimat,intent`) lalu jalankan `python evaluate.py --tema perpus`.

Periksa JSON Anda tanpa menjalankan aplikasi:

```bash
python -m json.tool themes/perpus.json
```

---

## 8. Pengaturan lewat variabel lingkungan

| Variabel | Bawaan | Fungsi |
| --- | --- | --- |
| `SECRET_KEY` | `ganti-dengan-kunci-rahasia` | Menandatangani cookie sesi. **Wajib diganti** di server sungguhan. |
| `THRESHOLD` | `0.45` | Ambang batas skor |
| `DATABASE` | `chat_history.db` | Lokasi file SQLite |
| `ADMIN_KEY` | (kosong) | Bila diisi, halaman admin hanya terbuka dengan `?key=<nilai>` |

Contoh:

```bash
# Linux / macOS
export ADMIN_KEY=rahasia123 THRESHOLD=0.4
python app.py
```

```powershell
# Windows PowerShell
$env:ADMIN_KEY="rahasia123"; $env:THRESHOLD="0.4"
python app.py
```

Lalu buka http://127.0.0.1:5000/admin/kampus?key=rahasia123

---

## 9. Menghentikan server

Tekan **Ctrl + C** di terminal tempat server berjalan. Nonaktifkan venv dengan `deactivate`.

---

## 10. Masalah yang sering terjadi

| Gejala | Penyebab | Solusi |
| --- | --- | --- |
| `'python' is not recognized` | Python belum masuk PATH | Pasang ulang dan centang *Add python.exe to PATH*, atau pakai `py` |
| `ModuleNotFoundError: No module named 'flask'` | venv belum aktif | Aktifkan venv, lalu `pip install -r requirements.txt` |
| `ModuleNotFoundError: No module named 'chatbot'` | Dijalankan dari folder yang salah | `cd aplikasi-final` dulu |
| `Address already in use` / port 5000 dipakai | Server lama masih jalan (di macOS bisa AirPlay Receiver) | Tutup server lama dengan Ctrl + C, atau `flask --app app run --port 5001` |
| `TemplateNotFound` | Nama folder bukan `templates` | Periksa ejaan folder dan nama file |
| `File tema xxx.json tidak valid` | Struktur tema salah | Baca daftar masalah di pesan galat, perbaiki file JSON |
| `json.decoder.JSONDecodeError` | Koma berlebih atau tanda kutip salah | `python -m json.tool themes/xxx.json` untuk melihat baris yang salah |
| `TypeError: unsupported operand type(s) for \|` | Python di bawah 3.10 | Pasang Python 3.10+ |
| Tampilan tidak berubah setelah CSS/JS diedit | Cache browser | Tekan Ctrl + Shift + R |
| Bot sering menjawab "Maaf, saya belum memahami" | Pola kurang bervariasi | Lihat halaman `/admin/<tema>`, tambahkan polanya ke JSON |
| Bot menjawab intent yang salah | Pola dua intent terlalu mirip | Centang Mode belajar, lihat skor kandidat, buat pola lebih spesifik |
