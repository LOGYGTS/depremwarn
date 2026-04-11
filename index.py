from flask import Flask, jsonify, render_template_string
import requests
import re
import random
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- GÜNCEL AYARLAR ---
TELEGRAM_TOKEN = "8661340862:AAF2uR2fwN0aSHES65xB7uswA1ceuQcZhw8"
CHAT_ID = "-1005272137007" 
LAST_NOTIFIED_ID = [None] 

# Ana sayfa tasarımı - JavaScript algoritması eklendi
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
        .quake-card { background: #334155; margin-bottom: 10px; padding: 12px; border-radius: 8px; border-left: 6px solid #3b82f6; cursor: pointer; }
        .risk-badge { font-size: 0.7rem; font-weight: bold; padding: 4px 8px; border-radius: 12px; text-transform: uppercase; }
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

        // --- RİSK ALGORİTMASI (JAVASCRIPT) ---
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
                            <b style="font-size:1.4rem">${q.mag}</b>
                            <span class="risk-badge" style="background: ${risk.color}22; color: ${risk.color}; border: 1px solid ${risk.color}">${risk.label}</span>
                        </div>
                        <div style="margin-top:5px;">${q.title}</div>
                        <div style="font-size:0.75rem; color:#94a3b8; margin-top:5px;">Saat: ${q.custom_hour} | Derinlik: ${q.depth}km</div>
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
    try:
        r = requests.post(url, data=payload, timeout=10)
        return r.json()
    except: return None

# Python tarafındaki risk algoritması (Bildirimler için)
def sismik_risk_etiketi(mag):
    mag = float(mag)
    if mag >= 4.0: return "🔴 RİSKLİ"
    elif mag >= 3.0: return "🟡 ORTA"
    return "🟢 GÜVENLİ"

@app.route('/')
def index():
    return render_template_string(HTML_SABLONU)

@app.route('/get_data')
def get_data():
    try:
        api_res = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live", timeout=10)
        api_data = api_res.json()
        k_res = requests.get("http://www.koeri.boun.edu.tr/scripts/lst6.asp", timeout=10)
        k_res.encoding = 'utf-8'
        soup = BeautifulSoup(k_res.text, 'html.parser')
        ham_saatler = re.findall(r'(\d{2}:\d{2}:\d{2})', soup.find('pre').text)

        if api_data.get("result"):
            ilk = api_data["result"][0]
            if ilk["earthquake_id"] != LAST_NOTIFIED_ID[0]:
                mag = float(ilk["mag"])
                if mag >= 1.5:
                    risk_txt = sismik_risk_etiketi(mag)
                    saat = ham_saatler[0] if ham_saatler else "--:--"
                    m = f"🔔 <b>YENİ DEPREM</b>\\n\\n📍 Yer: {ilk['title']}\\n📊 Büyüklük: <b>{mag}</b>\\n⏰ Saat: {saat}\\n🚦 Durum: {risk_txt}"
                    telegram_gonder(m)
                LAST_NOTIFIED_ID[0] = ilk["earthquake_id"]

            for i in range(len(api_data["result"])):
                q = api_data["result"][i]
                q["custom_hour"] = ham_saatler[i] if i < len(ham_saatler) else "00:00"
        return jsonify(api_data)
    except Exception as e:
        return jsonify({"result": [], "error": str(e)})

if __name__ == '__main__':
    app.run()
