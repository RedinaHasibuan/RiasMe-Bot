// =====================================================================
// Logika antarmuka chat: kirim pesan ke /api/chat dengan fetch()
// lalu tampilkan balasan tanpa memuat ulang halaman.
// Variabel THEME disediakan oleh templates/chat.html (Jinja2 + tojson).
// =====================================================================
const messagesEl = document.getElementById("messages");
const form = document.getElementById("chat-form");
const input = document.getElementById("chat-input");
const sendBtn = document.getElementById("send");
const counter = document.getElementById("count");
const btnClear = document.getElementById("btn-clear");
const learnMode = document.getElementById("learn-mode");
let sibuk = false;

const gulir = () => { messagesEl.scrollTop = messagesEl.scrollHeight; };

/** Ubah teks bot menjadi paragraf, daftar bernomor (1. ...), dan daftar poin (• ...). */
function renderRich(el, text) {
  let list = null, jenis = "";
  text.split("\n").forEach((baris) => {
    baris = baris.trim();
    if (!baris) { list = null; return; }
    const no = baris.match(/^\d+\.\s+(.*)/), poin = baris.match(/^[•-]\s+(.*)/);
    if (no || poin) {
      const k = no ? "ol" : "ul";
      if (!list || jenis !== k) { list = document.createElement(k); jenis = k; el.appendChild(list); }
      const li = document.createElement("li"), isi = (no || poin)[1];
      const label = isi.match(/^([A-Za-z]+):\s+(.*)/);
      if (label) {
        const kuat = document.createElement("strong");
        kuat.textContent = label[1] + ": ";
        li.append(kuat, label[2]);
      } else li.textContent = isi;
      list.appendChild(li);
    } else {
      list = null;
      const p = document.createElement("p");
      p.textContent = baris;
      el.appendChild(p);
    }
  });
}

/** Tambahkan satu gelembung pesan ke layar. */
function addMessage(sender, text, { meta = null, error = false } = {}) {
  const row = document.createElement("div");
  row.className = `row ${sender}`;
  if (sender === "bot") {
    const avatar = document.createElement("span");
    avatar.className = "avatar";
    avatar.setAttribute("aria-hidden", "true");
    avatar.textContent = THEME.avatar;
    row.appendChild(avatar);
  }
  const bubble = document.createElement("div");
  bubble.className = "bubble" + (error ? " error" : "");
  if (sender === "bot" && text) { bubble.classList.add("rich"); renderRich(bubble, text); }
  else bubble.textContent = text;         // textContent/createElement, BUKAN innerHTML -> aman dari XSS
  if (meta) {
    const small = document.createElement("small");
    small.className = "meta";
    small.textContent = meta;
    bubble.appendChild(small);
  }
  row.appendChild(bubble);
  messagesEl.appendChild(row);
  gulir();
  return bubble;
}

/** Indikator "sedang mengetik" berupa tiga titik. */
function addTyping() {
  const bubble = addMessage("bot", "");
  bubble.innerHTML = '<span class="dots" role="status" aria-label="Sedang mengetik"><span></span><span></span><span></span></span>';
  return bubble.parentElement;
}

/** Mode belajar: tampilkan 3 kandidat intent teratas di bawah jawaban. */
async function showCandidates(bubble, text) {
  try {
    const res = await fetch("/api/explain", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, theme: THEME.id }),
    });
    const data = await res.json();
    const list = document.createElement("ol");
    list.className = "candidates";
    data.candidates.forEach((c) => {
      const li = document.createElement("li");
      const lolos = c.score >= data.threshold ? "lolos ambang" : "di bawah ambang";
      li.textContent = `${c.intent} · ${c.score.toFixed(2)} (${lolos}) — pola “${c.pattern}”`;
      list.appendChild(li);
    });
    bubble.appendChild(list);
    gulir();
  } catch (err) {
    console.error(err);
  }
}

function updateControls() {
  sendBtn.disabled = sibuk || !input.value.trim();
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 120) + "px";
  input.style.overflowY = input.scrollHeight > 120 ? "auto" : "hidden";
  counter.hidden = input.value.length < 400;
  counter.textContent = `${input.value.length}/500`;
}

/** Kirim pesan ke server. */
async function sendMessage(text) {
  if (sibuk) return;
  sibuk = true;
  addMessage("user", text);
  input.value = "";
  updateControls();
  const typing = addTyping();

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, theme: THEME.id }),
    });
    const data = await res.json();
    typing.remove();

    if (!res.ok) {
      addMessage("bot", data.error || "Pesan belum bisa diproses.", { error: true });
      return;
    }
    const skor = data.score.toFixed(2);
    const meta = data.intent ? `intent: ${data.intent} · skor ${skor}` : `tidak dikenali · skor ${skor}`;
    const bubble = addMessage("bot", data.reply, { meta });
    if (learnMode.checked) await showCandidates(bubble, text);
  } catch (err) {
    typing.remove();
    addMessage("bot", "Pesanmu belum terkirim. Periksa koneksi, lalu coba lagi.", { error: true });
    console.error(err);
  } finally {
    sibuk = false;
    updateControls();
    input.focus();
  }
}

/** Muat riwayat percakapan saat halaman dibuka. */
async function loadHistory() {
  try {
    const res = await fetch(`/api/history/${THEME.id}`);
    const rows = await res.json();
    if (rows.length) { rows.forEach((r) => addMessage(r.sender, r.text)); return; }
  } catch (err) {
    console.error(err);
  }
  addMessage("bot", THEME.greeting);
}

// ---- Event listener ------------------------------------------------
form.addEventListener("submit", (e) => {
  e.preventDefault();                     // cegah form memuat ulang halaman
  const text = input.value.trim();
  if (text) sendMessage(text);
});
input.addEventListener("input", updateControls);
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); form.requestSubmit(); }
});
document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => sendMessage(chip.textContent));
});
learnMode.addEventListener("change", () => {
  document.body.classList.toggle("belajar", learnMode.checked);
  gulir();
});
btnClear.addEventListener("click", async () => {
  if (!confirm("Hapus seluruh riwayat percakapan?")) return;
  await fetch(`/api/history/${THEME.id}`, { method: "DELETE" });
  messagesEl.innerHTML = "";
  addMessage("bot", THEME.greeting);
});

// Kartu topik di landing page membuka chat dengan ?q=pertanyaan
function kirimPertanyaanDariUrl() {
  const q = new URLSearchParams(location.search).get("q");
  if (!q) return;
  history.replaceState(null, "", location.pathname);   // refresh tidak mengirim ulang
  sendMessage(q.slice(0, 500));
}

// Roda mouse menggeser baris chip ke samping (scrollbar disembunyikan)
const chipsEl = document.querySelector(".chips");
chipsEl.addEventListener("wheel", (e) => {
  if (e.deltaY) { chipsEl.scrollLeft += e.deltaY; e.preventDefault(); }
}, { passive: false });

loadHistory().then(kirimPertanyaanDariUrl);
input.focus();
