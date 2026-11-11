"""Uji unit untuk mesin chatbot RiasMe (tanpa Flask)."""
import csv
from pathlib import Path

import pytest

from chatbot.engine import ChatbotEngine, load_themes, preprocess, similarity, validate_theme

BASE_DIR = Path(__file__).resolve().parent.parent
THEMES = load_themes(BASE_DIR / "themes")
RIASME = THEMES["riasme"]


# --------------------------------------------------------------------------- #
# Praproses dan skor kemiripan
# --------------------------------------------------------------------------- #
def test_preprocess_normalisasi_dan_stopword():
    assert preprocess("Gimana urutan makeup di muka berminyak, kak?") == \
        ["bagaimana", "urutan", "makeup", "wajah", "berminyak"]


def test_preprocess_kata_gaul_tema_makeup():
    assert preprocess("make up") == ["makeup"]
    assert preprocess("mukaku") == ["wajah"]
    assert preprocess("foundie gumpal") == ["foundation", "menggumpal"]


def test_similarity_kalimat_sama_bernilai_satu():
    t = ["makeup", "cakey"]
    assert similarity(t, t) == 1.0


def test_similarity_kalimat_berbeda_rendah():
    assert similarity(["nasi"], ["makeup", "cakey"]) < 0.3


# --------------------------------------------------------------------------- #
# Struktur tema
# --------------------------------------------------------------------------- #
def test_tema_riasme_termuat():
    assert "riasme" in THEMES


def test_tema_memenuhi_syarat_minimal():
    assert len(RIASME["intents"]) >= 10
    assert len(RIASME["suggestions"]) >= 4
    assert len(RIASME["fallback"]) >= 2
    for intent in RIASME["intents"]:
        assert len(intent["patterns"]) >= 5, f"{intent['tag']}: pola kurang dari 5"
        assert len(intent["responses"]) >= 2, f"{intent['tag']}: respons kurang dari 2"


def test_semua_tema_bawaan_valid():
    for theme in THEMES.values():
        assert validate_theme(theme) == []


def test_validate_theme_menemukan_kesalahan():
    rusak = {"id": "x", "name": "X", "bot_name": "B", "avatar": "*", "color": "#000",
             "description": "d", "greeting": "g", "suggestions": [], "fallback": ["f"],
             "intents": [{"tag": "a", "patterns": ["halo"], "responses": ["hai"]},
                         {"tag": "b", "patterns": ["halo"], "responses": []}]}
    masalah = validate_theme(rusak)
    assert any("responses kosong" in m for m in masalah)
    assert any("'a' dan 'b'" in m for m in masalah)


# --------------------------------------------------------------------------- #
# Klasifikasi intent
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("pesan, intent", [
    ("halo", "salam"),
    ("makasih", "terima_kasih"),
    ("makeup murah", "budget_makeup_pemula"),
    ("urutan makeup kulit berminyak", "urutan_kulit_berminyak"),
    ("urutan makeup kulit kering", "urutan_kulit_kering"),
    ("cushion vs foundation", "beda_foundie_cushion"),
    ("cara pilih shade", "cara_pilih_shade"),
    ("apa itu undertone", "undertone"),
    ("makeup cakey", "makeup_cakey"),
    ("foundation jadi gelap", "foundation_teroksidasi"),
    ("lipstik cepat pudar", "lipstik_pudar"),
    ("cara mencuci brush makeup", "kebersihan_alat_makeup"),
    ("makeup kedaluwarsa", "keamanan_kedaluwarsa_produk"),
    ("foundie menggumpal", "makeup_cakey"),          # kata gaul dinormalisasi
])
def test_klasifikasi_intent(pesan, intent):
    tag, _ = ChatbotEngine(RIASME).classify(pesan)
    assert tag == intent


def test_salah_ketik_masih_dikenali():
    tag, _ = ChatbotEngine(RIASME).classify("lipstik cepat pudr")
    assert tag == "lipstik_pudar"


def test_setiap_pola_mengenali_intent_sendiri():
    """Tidak boleh ada pola yang lebih mirip dengan intent lain."""
    engine = ChatbotEngine(RIASME)
    salah = []
    for intent in RIASME["intents"]:
        for pola in intent["patterns"]:
            tag, _ = engine.classify(pola)
            if tag != intent["tag"]:
                salah.append((pola, intent["tag"], tag))
    assert salah == []


def test_pertanyaan_di_luar_tema_memberi_fallback():
    hasil = ChatbotEngine(RIASME).reply("siapa pemenang piala dunia")
    assert hasil["intent"] is None
    assert hasil["reply"] in RIASME["fallback"]


def test_pesan_kosong_tidak_error():
    hasil = ChatbotEngine(RIASME).reply("   ")
    assert hasil["intent"] is None


def test_placeholder_nama_bot_diganti():
    hasil = ChatbotEngine(RIASME).reply("kamu siapa")
    assert "{nama_bot}" not in hasil["reply"]
    assert "RiasMe" in hasil["reply"]


def test_explain_mengurutkan_kandidat_dari_skor_tertinggi():
    kandidat = ChatbotEngine(RIASME).explain("urutan makeup kulit berminyak")
    assert kandidat[0]["intent"] == "urutan_kulit_berminyak"
    assert kandidat[0]["pattern"] == "urutan makeup kulit berminyak"
    skor = [k["score"] for k in kandidat]
    assert skor == sorted(skor, reverse=True)


# --------------------------------------------------------------------------- #
# Data uji dan akurasi
# --------------------------------------------------------------------------- #
def test_data_uji_hanya_memakai_intent_yang_ada():
    from evaluate import baca_data
    tag_tema = {i["tag"] for i in RIASME["intents"]} | {"fallback"}
    assert {intent for _, intent in baca_data("riasme")} <= tag_tema


def test_akurasi_data_uji_riasme_minimal_90_persen():
    from evaluate import baca_data, evaluasi
    akurasi, _ = evaluasi(RIASME, baca_data("riasme"), 0.45)
    assert akurasi >= 0.9
