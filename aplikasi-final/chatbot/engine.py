"""
Mesin chatbot berbasis aturan (rule-based).

Alur kerja:
1. Praproses  : huruf kecil -> buang tanda baca -> normalisasi kata tidak baku
                -> buang kata henti (stopword).
2. Pencocokan : setiap pola pada setiap intent diberi skor kemiripan
                (gabungan Jaccard, kemiripan karakter/difflib, dan cakupan).
3. Keputusan  : intent dengan skor tertinggi dipilih jika skornya >= ambang batas;
                jika tidak, chatbot memberi respons fallback.
"""
import json
import random
import re
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

# Kamus normalisasi kata tidak baku -> baku (silakan ditambah sesuai tema)
NORMALISASI = {
    "gak": "tidak", "ga": "tidak", "nggak": "tidak", "enggak": "tidak", "tdk": "tidak",
    "gimana": "bagaimana", "gmn": "bagaimana", "bgmn": "bagaimana",
    "dmn": "dimana", "brp": "berapa", "berapakah": "berapa",
    "yg": "yang", "dgn": "dengan", "utk": "untuk", "buat": "untuk",
    "sy": "saya", "aku": "saya", "gue": "saya", "gw": "saya",
    "kak": "", "min": "", "dong": "", "sih": "", "nih": "", "ya": "", "yah": "",
    "makasih": "terima kasih", "thanks": "terima kasih", "thx": "terima kasih",
    "hai": "halo", "hi": "halo", "hello": "halo", "hallo": "halo",
    # --- Kata khusus tema RiasMe (makeup) ---
    "muka": "wajah", "mukaku": "wajah", "wajahku": "wajah", "kulitku": "kulit",
    "gumpal": "menggumpal", "nempel": "menempel", "jerawatan": "berjerawat",
    "dandan": "makeup", "make": "makeup", "up": "",          # "make up" -> "makeup"
    "foundie": "foundation", "fdt": "foundation",
    "lipstick": "lipstik", "lipcream": "lipstik",
    "difoto": "foto", "keabuan": "keabu abuan",
    "hapus": "membersihkan", "menghapus": "membersihkan",
    "ngga": "tidak", "ngak": "tidak", "donk": "", "ku": "",
}

# Kata henti (stopword) bahasa Indonesia yang sederhana
STOPWORDS = {
    "yang", "di", "ke", "dari", "dan", "atau", "itu", "ini", "untuk", "dengan",
    "adalah", "apa", "saya", "mau", "ingin", "tolong", "bisa", "boleh", "kah",
    "pada", "akan", "juga", "ada", "tentang", "mohon", "info", "informasi",
}

# --- Pemahaman konteks sederhana (jenis kulit + topik terakhir) ---
JENIS_KULIT = ("berminyak", "kering", "kombinasi", "normal")
# Kata yang boleh ada pada pertanyaan lanjutan seperti "kalau untuk kulit kering gimana?"
PENGISI_LANJUTAN = {"kulit", "wajah", "kalau", "bagaimana", "jenis", "tipe", "yang", "jadi",
                    "lalu", "terus", "kasih", "tahu", "bagus", "sendiri"} | set(JENIS_KULIT)
TAG_NETRAL = {"salam", "perkenalan_bot", "terima_kasih"}
_LABEL_KULIT = re.compile(r"(Berminyak|Kering|Kombinasi|Normal):\s*")


def pisah_per_jenis_kulit(teks: str):
    """Pecah respons berlabel ('Berminyak: ... Kering: ...') menjadi (pembuka, {jenis: isi}, penutup)."""
    cocok = list(_LABEL_KULIT.finditer(teks))
    if len(cocok) < 3:
        return None
    isi = {}
    for i, m in enumerate(cocok):
        akhir = cocok[i + 1].start() if i + 1 < len(cocok) else len(teks)
        isi[m.group(1).lower()] = teks[m.end():akhir].strip()
    penutup, terakhir = "", list(isi)[-1]
    potong = re.search(r"\.\s+(?=[A-Z])", isi[terakhir])   # kalimat setelah label terakhir = catatan umum
    if potong:
        penutup = isi[terakhir][potong.end():].strip()
        isi[terakhir] = isi[terakhir][:potong.start() + 1].strip()
    return teks[:cocok[0].start()].strip(), isi, penutup


# Bobot tiga ukuran kemiripan (jumlahnya harus 1)
BOBOT_JACCARD, BOBOT_FUZZY, BOBOT_CAKUPAN = 0.4, 0.3, 0.3

KUNCI_WAJIB_TEMA = ["id", "name", "bot_name", "avatar", "color", "description",
                    "greeting", "suggestions", "fallback", "intents"]


def preprocess(teks: str) -> list[str]:
    """Ubah kalimat mentah menjadi daftar token yang sudah dinormalisasi."""
    teks = teks.lower()
    teks = re.sub(r"[^a-z0-9\s]", " ", teks)          # buang tanda baca & emoji
    tokens = []
    for kata in teks.split():
        kata = NORMALISASI.get(kata, kata)
        for k in kata.split():                       # normalisasi bisa jadi 2 kata
            if k and k not in STOPWORDS:
                tokens.append(k)
    return tokens


def similarity(tokens_a: list[str], tokens_b: list[str]) -> float:
    """Skor kemiripan 0..1 antara token pesan (a) dan token pola (b)."""
    if not tokens_a or not tokens_b:
        return 0.0
    set_a, set_b = set(tokens_a), set(tokens_b)
    # 1) Jaccard: proporsi kata yang sama dari seluruh kata gabungan
    jaccard = len(set_a & set_b) / len(set_a | set_b)
    # 2) Kemiripan karakter: tahan terhadap salah ketik ("jadwl" ~ "jadwal")
    fuzzy = SequenceMatcher(None, " ".join(tokens_a), " ".join(tokens_b)).ratio()
    # 3) Cakupan: berapa bagian kata pola yang muncul di pesan
    cakupan = len(set_a & set_b) / len(set_b)
    return round(BOBOT_JACCARD * jaccard + BOBOT_FUZZY * fuzzy + BOBOT_CAKUPAN * cakupan, 4)


def validate_theme(theme: dict) -> list[str]:
    """Periksa struktur file tema. Kembalikan daftar masalah (kosong = valid)."""
    masalah = [f"kunci '{k}' tidak ada" for k in KUNCI_WAJIB_TEMA if k not in theme]
    if masalah:
        return masalah
    if not theme["fallback"]:
        masalah.append("daftar 'fallback' kosong")
    tags, pola_milik = set(), {}
    for i, intent in enumerate(theme["intents"]):
        for k in ("tag", "patterns", "responses"):
            if k not in intent:
                masalah.append(f"intent ke-{i + 1}: kunci '{k}' tidak ada")
        tag = intent.get("tag", f"#{i + 1}")
        if tag in tags:
            masalah.append(f"tag '{tag}' dipakai lebih dari sekali")
        tags.add(tag)
        if not intent.get("patterns"):
            masalah.append(f"intent '{tag}': patterns kosong")
        if not intent.get("responses"):
            masalah.append(f"intent '{tag}': responses kosong")
        for pola in intent.get("patterns", []):
            kunci = " ".join(preprocess(pola))
            if not kunci:
                masalah.append(f"intent '{tag}': pola '{pola}' kosong setelah praproses")
            elif kunci in pola_milik and pola_milik[kunci] != tag:
                masalah.append(f"pola '{pola}' ada di intent '{pola_milik[kunci]}' dan '{tag}'")
            pola_milik.setdefault(kunci, tag)
    return masalah


def load_themes(folder: str | Path) -> dict[str, dict]:
    """Baca semua file tema *.json di folder dan kembalikan dict {id_tema: data}."""
    themes = {}
    for path in sorted(Path(folder).glob("*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        masalah = validate_theme(data)
        if masalah:
            raise ValueError(f"File tema {path.name} tidak valid:\n- " + "\n- ".join(masalah))
        themes[data["id"]] = data
    return themes


class ChatbotEngine:
    """Satu objek engine melayani satu tema."""

    def __init__(self, theme: dict, threshold: float = 0.45):
        self.theme = theme
        self.threshold = threshold
        # Praproses semua pola sekali saja saat engine dibuat (lebih cepat)
        self._patterns = [
            (intent["tag"], pola, preprocess(pola))
            for intent in theme["intents"]
            for pola in intent["patterns"]
        ]
        self._responses = {i["tag"]: i["responses"] for i in theme["intents"]}
        # Intent yang jawabannya berlabel jenis kulit (bisa dipersonalisasi)
        self._berlabel = {t for t, rs in self._responses.items() if any(pisah_per_jenis_kulit(r) for r in rs)}

    def explain(self, pesan: str, top: int = 3) -> list[dict]:
        """Kandidat intent terbaik beserta pola dan skornya (untuk belajar/debug)."""
        tokens = preprocess(pesan)
        terbaik = {}
        for tag, pola, pola_tokens in self._patterns:
            skor = similarity(tokens, pola_tokens)
            if tag not in terbaik or skor > terbaik[tag]["score"]:
                terbaik[tag] = {"intent": tag, "pattern": pola, "score": skor}
        return sorted(terbaik.values(), key=lambda x: x["score"], reverse=True)[:top]

    def classify(self, pesan: str) -> tuple[str | None, float]:
        """Kembalikan (tag_intent, skor). tag None jika di bawah ambang."""
        kandidat = self.explain(pesan, top=1)
        if not kandidat:
            return None, 0.0
        best = kandidat[0]
        if best["score"] < self.threshold:
            return None, best["score"]
        return best["intent"], best["score"]

    def _isi_placeholder(self, teks: str) -> str:
        """Ganti placeholder dinamis, misalnya {waktu} dan {tanggal}."""
        now = datetime.now()
        return (teks.replace("{waktu}", now.strftime("%H:%M"))
                    .replace("{tanggal}", now.strftime("%d-%m-%Y"))
                    .replace("{nama_bot}", self.theme["bot_name"]))

    def _format_jenis_kulit(self, teks: str, kulit: str | None) -> str:
        """Jawaban berlabel: tampilkan bagian jenis kulit pengguna, atau daftar semua jenis."""
        hasil = pisah_per_jenis_kulit(teks)
        if not hasil:
            return teks
        pembuka, isi, penutup = hasil
        baris = [pembuka] if pembuka else []
        if kulit in isi:
            baris.append(f"Untuk kulit {kulit}: {isi[kulit]}")
        else:
            baris.append("Tergantung jenis kulitmu:")
            baris += [f"• {j.capitalize()}: {t}" for j, t in isi.items()]
        if penutup:
            baris.append(penutup)
        if kulit not in isi:
            baris.append("Sebutkan jenis kulitmu (misalnya “kulitku kering”), nanti kujawab lebih spesifik.")
        return "\n".join(baris)

    def _pilih_respons(self, tag: str) -> str:
        """Acak satu respons; untuk intent urutan_* utamakan yang berbentuk daftar bernomor."""
        pilihan = self._responses[tag]
        if tag.startswith("urutan_"):
            pilihan = [r for r in pilihan if "\n1. " in r] or pilihan
        return random.choice(pilihan)

    def _topik_lanjutan(self, topik: str | None, kulit: str) -> str | None:
        """Pertanyaan lanjutan 'kalau kulit kering?' -> topik sebelumnya, atau urutan makeup."""
        if topik in self._berlabel:
            return topik
        tujuan = f"urutan_kulit_{kulit}"
        return tujuan if tujuan in self._responses else None

    def reply(self, pesan: str, konteks: dict | None = None) -> dict:
        """Proses pesan pengguna. `konteks` = {"kulit": ..., "topik": ...} dari balasan sebelumnya."""
        konteks = dict(konteks or {})
        if not pesan or not pesan.strip():
            return {"reply": "Pesannya masih kosong. Silakan ketik pertanyaan Anda.",
                    "intent": None, "score": 0.0, "context": konteks}
        tokens = preprocess(pesan)
        kulit = next((t for t in tokens if t in JENIS_KULIT), None)
        if kulit:
            konteks["kulit"] = kulit
        tag, skor = self.classify(pesan)
        if kulit and set(tokens) <= PENGISI_LANJUTAN:                 # hanya menyebut jenis kulit
            lanjut = self._topik_lanjutan(konteks.get("topik"), kulit)
            if lanjut:
                tag, skor = lanjut, max(skor, self.threshold)
        elif kulit and tag and tag.startswith("urutan_kulit_") and f"urutan_kulit_{kulit}" in self._responses:
            tag = f"urutan_kulit_{kulit}"                              # samakan dengan jenis kulit yang disebut
        if tag is None:
            teks = random.choice(self.theme["fallback"])
        else:
            teks = self._format_jenis_kulit(self._pilih_respons(tag), konteks.get("kulit"))
            if tag not in TAG_NETRAL:
                konteks["topik"] = tag
        return {"reply": self._isi_placeholder(teks), "intent": tag, "score": skor, "context": konteks}
