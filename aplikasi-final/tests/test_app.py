"""Uji integrasi route Flask menggunakan test client."""
import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    # Database sementara agar pengujian tidak mengotori data asli
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.db")})
    return app.test_client()


def test_halaman_utama_menampilkan_tema(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "Panduan Makeup Pemula" in res.get_data(as_text=True)


def test_halaman_chat(client):
    res = client.get("/chat/riasme")
    assert res.status_code == 200
    assert "RiasMe" in res.get_data(as_text=True)


def test_tema_tidak_ada_404(client):
    assert client.get("/chat/tidak-ada").status_code == 404
    assert client.get("/api/history/tidak-ada").status_code == 404


def test_api_themes(client):
    data = client.get("/api/themes").get_json()
    assert len(data) == 1
    assert data[0]["id"] == "riasme"


def test_api_chat_berhasil(client):
    res = client.post("/api/chat", json={"message": "urutan makeup kulit berminyak", "theme": "riasme"})
    assert res.status_code == 200
    data = res.get_json()
    assert data["intent"] == "urutan_kulit_berminyak"
    assert data["reply"]


def test_api_chat_fallback_untuk_pertanyaan_di_luar_tema(client):
    data = client.post("/api/chat", json={"message": "siapa pemenang piala dunia", "theme": "riasme"}).get_json()
    assert data["intent"] is None
    assert data["reply"]


@pytest.mark.parametrize("payload", [
    {"message": "", "theme": "riasme"},
    {"message": "halo", "theme": "salah"},
    {"message": "a" * 501, "theme": "riasme"},
    {},
])
def test_api_chat_input_tidak_valid(client, payload):
    assert client.post("/api/chat", json=payload).status_code == 400


def test_riwayat_tersimpan_dan_bisa_dihapus(client):
    client.post("/api/chat", json={"message": "halo", "theme": "riasme"})
    riwayat = client.get("/api/history/riasme").get_json()
    assert [r["sender"] for r in riwayat] == ["user", "bot"]

    client.delete("/api/history/riasme")
    assert client.get("/api/history/riasme").get_json() == []


def test_statistik_intent(client):
    client.post("/api/chat", json={"message": "halo", "theme": "riasme"})
    stats = client.get("/api/stats/riasme").get_json()
    assert stats[0]["intent"] == "salam"


def test_api_explain(client):
    data = client.post("/api/explain", json={"message": "makeup cakey", "theme": "riasme"}).get_json()
    assert data["threshold"] == 0.45
    assert data["candidates"][0]["intent"] == "makeup_cakey"


def test_halaman_admin_menampilkan_pertanyaan_tak_dikenali(client):
    client.post("/api/chat", json={"message": "harga bensin berapa", "theme": "riasme"})
    html = client.get("/admin/riasme").get_data(as_text=True)
    assert "harga bensin berapa" in html
    assert "tidak dikenali" in html


def test_admin_key_melindungi_halaman_admin(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "t.db"), "ADMIN_KEY": "rahasia"})
    c = app.test_client()
    assert c.get("/admin/riasme").status_code == 403
    assert c.get("/api/stats/riasme").status_code == 403
    assert c.get("/admin/riasme?key=rahasia").status_code == 200
