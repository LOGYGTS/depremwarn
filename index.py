from flask import Flask, jsonify, render_template_string, request
import requests

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = "8661340862:AAF2uR2fwN0aSHES65xB7uswA1ceuQcZhw8"
CHAT_ID = "~1003826426476" 

# ANA SAYFAYA TEST BUTONU EKLEDİM
HTML_SABLONU = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8"><title>Sismik Panel</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { font-family: sans-serif; margin: 0; background: #0f172a; color: white; display: flex; flex-direction: column; height: 100vh; }
        header { background: #1e293b; padding: 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #334155; }
        .main { display: flex; flex: 1; overflow: hidden; }
        #map { flex: 2; height: 100%; }
        .sidebar { flex: 0.8; background: #111827; overflow-y: auto; padding: 10px; }
        .btn-test { background: #ef4444; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; font-weight: bold; }
        @media (max-width: 768px) { .main { flex-direction: column; } #map { height: 40%; } }
    </style>
</head>
<body>
    <header>
        <div>📡 SİSMİK PANEL</div>
        <button class="btn-test" onclick="location.href='/manuel_test'">GRUPTA TEST MESAJI AT</button>
    </header>
    <div class="main"><div id="map"></div><div class="sidebar" id="liste">Yükleniyor...</div></div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        let map = L.map('map').setView([39.0, 35.0], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        async function update() {
            const res = await fetch('/get_data');
            const data = await res.json();
            let h = "";
            data.result.slice(0, 20).forEach(q => {
                h += `<div style="background:#1f2937; margin-bottom:5px; padding:10px; border-radius:5px;"><b>${q.mag}</b> - ${q.title}</div>`;
            });
            document.getElementById('liste').innerHTML = h;
        }
        update(); setInterval(update, 30000);
    </script>
</body>
</html>
"""

def tg_send(m):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    return requests.post(url, data={"chat_id": CHAT_ID, "text": m, "parse_mode": "HTML"}).json()

@app.route('/')
def index(): return render_template_string(HTML_SABLONU)

# HARİTADAKİ KIRMIZI BUTONA BASINCA ÇALIŞIR
@app.route('/manuel_test')
def manuel_test():
    sonuc = tg_send("🔴 <b>MANUEL SİSTEM TESTİ</b>\\nHarita üzerinden tetiklendi. Bot şu an grupta yetkili!")
    return f"Telegram Yanıtı: {sonuc}"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        upd = request.get_json()
        if "message" in upd and "text" in upd["message"]:
            if "/test" in upd["message"]["text"].lower():
                tg_send("✅ <b>WEBHOOK TESTİ BAŞARILI!</b>\\nBot mesajı aldı ve cevap veriyor.")
    except: pass
    return "OK", 200

@app.route('/get_data')
def get_data():
    r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live").json()
    return jsonify(r)

if __name__ == '__main__': app.run()
