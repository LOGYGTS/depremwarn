from flask import Flask, jsonify, render_template_string, request
import requests
import re
import random
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = "8661340862:AAF2uR2fwN0aSHES65xB7uswA1ceuQcZhw8"
CHAT_ID = "-5272137007" 
LAST_NOTIFIED_ID = [None]

# Harita ve Risk Algoritması Paneli
HTML_SABLONU = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sismik Risk Paneli</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #0f172a; color: white; overflow: hidden; }
        header { background: #1e293b; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #3b82f6; }
        #live-clock { font-family: monospace; font-size: 1.2rem; color: #60a5fa; }
        .dashboard { display: flex; flex-direction: column; height: calc(100vh - 55px); }
        #map { height: 40vh; width: 100%; border-bottom: 1px solid #334155; }
        .sidebar { flex: 1; background: #1e293b; overflow-y: auto; padding: 10px; }
        .quake-card { background: #334155; margin-bottom: 10px; padding: 12px; border-radius: 8px; border-left: 5px solid #3b82f6; cursor: pointer; }
        .risk-badge { font-size: 0.7rem; font-weight: bold; padding: 4px 8px; border-radius: 12px; }
        @media (min-width: 768px) { .dashboard { flex-direction: row; } #map { height: 100%; flex: 2; border-right: 1px solid #334155; } }
    </style>
</head>
<body>
    <header><h1>📡 SİSMİK RİSK ANALİZİ</h1><div id="live-clock">00:00:00</div></header>
    <div class="dashboard"><div id="map"></div><div class="sidebar" id="liste">Yükleniyor...</div></div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        let map = L.map('map').setView([39.0, 35.0], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        let marker = L.marker([39.0, 35.0]).addTo(map);
        setInterval(() => { document.getElementById('live-clock').innerText = new Date().toLocaleTimeString('tr-TR'); }, 1000);
        function getRisk(mag) {
            if (mag >= 4.0) return { label: "RİSKLİ", color: "#ff4444" };
            if (mag >= 3.0) return { label: "ORTA", color: "#ffbb33" };
            return { label: "GÜVENLİ", color: "#00C851" };
        }
        async function updateData() {
            try {
                const res = await fetch('/get_data');
                const data = await res.json();
                let html = "";
                data.result.slice(0, 30).forEach((q) => {
                    const risk = getRisk(parseFloat(q.mag));
                    const coords = q.geojson.coordinates;
                    html += `<div class="quake-card" style="border-left-color: ${risk.color}" onclick="map.setView([${coords[1]},${coords[0]}],10); marker.setLatLng([${coords[1]},${coords[0]}]).bindPopup('${q.title}').openPopup();">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <b>${q.mag}</b>
                            <span class="risk-badge" style="color: ${risk.color}; border: 1px solid ${risk.color}">${risk.label}</span>
                        </div>
                        <div style="margin-top:5px; font-size:0.9rem">${q.title}</div>
                    </div>`;
                });
                document.getElementById('liste').innerHTML = html;
            } catch(e) { console.error(e); }
        }
        updateData(); setInterval(updateData, 30000);
    </script>
</body>
</html>
"""

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"}
    requests.post(url, data=payload, timeout=5)

def get_son_deprem_mesaj():
    api_res = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live", timeout=10).json()
    if api_res.get("result"):
        son = api_res["result"][0]
        mag = float(son["mag"])
        risk = "🔴 RİSKLİ" if mag >= 4.0 else ("🟡 ORTA" if mag >= 3.0 else "🟢 GÜVENLİ")
        return f"🚀 <b>SON DEPREM BİLGİSİ</b>\\n\\n📍 Yer: {son['title']}\\n📊 Büyüklük: {mag}\\n📉 Derinlik: {son['depth']}km\\n🚦 Durum: {risk}"
    return "Veri alınamadı."

@app.route('/')
def index():
    return render_template_string(HTML_SABLONU)

# TELEGRAM'DAN GELEN KOMUTLARI DİNLEYEN KISIM
@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if "message" in update and "text" in update["message"]:
        text = update["message"]["text"]
        if text.startswith("/test"):
            mesaj = get_son_deprem_mesaj()
            telegram_gonder(mesaj)
    return "OK", 200

@app.route('/get_data')
def get_data():
    try:
        api_res = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live", timeout=10).json()
        # Otomatik bildirim kontrolü
        if api_res.get("result"):
            ilk = api_res["result"][0]
            if ilk["earthquake_id"] != LAST_NOTIFIED_ID[0]:
                if float(ilk["mag"]) >= 1.5:
                    telegram_gonder(f"🔔 <b>YENİ DEPREM</b>\\n\\n📍 Yer: {ilk['title']}\\n📊 Büyüklük: {ilk['mag']}")
                LAST_NOTIFIED_ID[0] = ilk["earthquake_id"]
        return jsonify(api_res)
    except: return jsonify({"result": []})

if __name__ == '__main__':
    app.run()
