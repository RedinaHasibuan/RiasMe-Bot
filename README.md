# Chatbot Tematik dengan Flask

Paket kode praktikum Aplikasi Web untuk membangun **chatbot tematik berbasis aturan (rule-based)**
dengan Python dan Flask, mulai dari program "Halo, Flask!" sampai aplikasi lengkap dengan
tiga tema, REST API, riwayat SQLite, halaman statistik, evaluasi akurasi, dan 34 uji otomatis.

> Panduan langkah demi langkah cara menjalankan ada di **[CARA-MENJALANKAN.md](CARA-MENJALANKAN.md)**.

## Mulai cepat (aplikasi final)

```bash
cd aplikasi-final
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
python app.py
```

Buka **http://127.0.0.1:5000** di browser.

## Isi paket

```
chatbot-tematik-flask/
├── README.md                      ← file ini
├── CARA-MENJALANKAN.md            ← panduan lengkap menjalankan setiap tahap
├── requirements.txt               ← Flask + pytest (cukup untuk semua tahap)
├── template-tema.json             ← kerangka untuk membuat tema Anda sendiri
├── tahapan/                       ← belajar bertahap, setiap folder bisa dijalankan sendiri
│   ├── tahap-01-halo-flask/          route, variabel URL, query string, JSON
│   ├── tahap-02-template-dan-form/   Jinja2, form POST, "bot beo"
│   ├── tahap-03-chatbot-terminal/    mesin chatbot v1 (kata kunci) vs v2 (kemiripan)
│   ├── tahap-04-api-json/            chatbot sebagai REST API POST /api/chat
│   └── tahap-05-antarmuka-chat/      halaman chat dengan fetch(), tanpa reload
└── aplikasi-final/                ← TAHAP 6: aplikasi lengkap
    ├── app.py                        route halaman + REST API + halaman admin
    ├── cli.py                        chat di terminal (python cli.py --debug)
    ├── evaluate.py                   ukur akurasi dengan data uji
    ├── chatbot/engine.py             praproses, skor kemiripan, validasi tema
    ├── chatbot/database.py           riwayat & statistik (SQLite)
    ├── themes/                       kampus.json, kuliner.json, wisata.json
    ├── evaluasi/                     data uji CSV per tema
    ├── templates/ static/            HTML (Jinja2), CSS, JavaScript
    └── tests/                        34 uji pytest
```

## Peta tahapan

| Tahap | Yang dipelajari | Hasil yang bisa dicoba |
| --- | --- | --- |
| 1 | Route, fungsi view, variabel URL, query string, `jsonify` | `/halo/Budi`, `/cari?q=krs`, `/api/info` |
| 2 | Template Jinja2, pewarisan template, form GET/POST | "Bot beo" yang membalas dengan memuat ulang halaman |
| 3 | Praproses teks, skor kemiripan, ambang batas | Chat di terminal, perbandingan v1 vs v2 |
| 4 | REST API, validasi input, kode status HTTP | `POST /api/chat` diuji dengan `uji_api.py` / curl |
| 5 | JavaScript `fetch()`, DOM, `async/await` | Halaman chat tanpa reload |
| 6 | Multi tema, sesi, SQLite, admin, pengujian, evaluasi | Aplikasi final |

## Endpoint aplikasi final

| Metode | URL | Keterangan |
| --- | --- | --- |
| GET | `/` | Halaman pilih tema |
| GET | `/chat/<tema>` | Halaman chat satu tema |
| GET | `/admin/<tema>` | Statistik & pertanyaan yang tidak dikenali |
| GET | `/api/themes` | Daftar tema |
| POST | `/api/chat` | `{"message": "...", "theme": "kampus"}` → `{"reply", "intent", "score"}` |
| POST | `/api/explain` | Tiga kandidat intent teratas beserta skornya |
| GET | `/api/history/<tema>` | Riwayat chat sesi ini |
| DELETE | `/api/history/<tema>` | Hapus riwayat sesi ini |
| GET | `/api/stats/<tema>` | Jumlah pertanyaan per intent |

## Lisensi dan catatan

Kode untuk keperluan pembelajaran. Isi jawaban di file tema bersifat umum/contoh
(misalnya email `kampus-contoh.ac.id`); sesuaikan dengan data institusi Anda sebelum dipakai sungguhan.
