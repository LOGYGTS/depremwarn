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

# Ana Sayfa Tasarımı (Harita ve Liste)
HTML_SABLONU = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sismik Risk Paneli</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #0f172a; color: white; overflow-x: hidden; }
        header { background: #1e293b; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #3b82f6; position: sticky; top: 0; z-index: 1000; }
        h1 { margin: 0; font-size: 1.2rem; }
        #live-clock { font-family: monospace; font-size: 1.2rem; color: #60a5fa; }
        .dashboard { display: flex; flex-direction: column; height: calc(100vh - 60px); }
        #map { height: 45vh; width: 100%; border-bottom: 2px solid #334155; }
        .sidebar { flex: 1; background: #1e293b; overflow-y: auto; padding: 10px; }
        .quake-card { background: #334155; margin-bottom: 10px; padding: 12px; border-radius: 8px; border-left: 5px solid #3b82f6; cursor: pointer; }
        .risk-indicator { font-size: 0.7rem; font-weight: bold; padding: 3px 7px; border-radius: 12px; background: rgba(0,0,0,0.3); }
        @media (min-width: 768px) {
            .dashboard { flex-direction: row; }
            #map { height: 100%; flex: 2; border-bottom: none; border-right: 2px solid #334155; }
            .sidebar { flex: 1; }
        }
    </style>
</head>
<body>
    <header><h1>📡 SİSMİK RİSK ANALİZİ</h1><div id="live-clock">00:00:00</div></header>
    <div class="dashboard"><div id="map"></div><div class="sidebar" id="liste">Veriler yükleniyor...</div></div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        let map = L.map('map').setView([39.0, 35.0], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        let marker = L.marker([39.0, 35.0]).addTo(map);
        
        setInterval(() => { document.getElementById('live-clock').innerText = new Date().toLocaleTimeString('tr-TR'); }, 1000);

        async function updateData() {
            try {
                const res = await fetch('/get_data');
                const data = await res.json();
                if(!data.result || data.result.length === 0) return;
                
                let html = "";
                data.result.slice(0, 40).forEach((q) => {
                    const coords = q.geojson.coordinates;
                    const risk = q.risk_analysis || {status: "Bilinmiyor", color: "#666"};
                    html += `<div class="quake-card" onclick="map.setView([${coords[1]},${coords[0]}], 10); marker.setLatLng([${coords[1]},${coords[0]}]).bindPopup('${q.title}').openPopup();">
                        <div style="display:flex; justify-content:space-between; align-items:center;">
                            <b style="font-size:1.3rem">${q.mag}</b>
                            <span class="risk-indicator" style="color:${risk.color}">${risk.status}</span>
                        </div>
                        <div style="font-size:0.9rem; margin-top:5px;">${q.title}</div>
                        <div style="font-size:0.75rem; color:#94a3b8">Saat: ${q.custom_hour} | Derinlik: ${q.depth}km</div>
                    </div>`;
                });
                document.getElementById('liste').innerHTML = html;
            } catch(e) { console.error("Veri hatası:", e); }
        }
        updateData(); setInterval(updateData, 20000);
    </script>
</body>
</html>
"""

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=5)
    except: pass

def sismik_risk_etiketi(mag, derinlik):
    mag = float(mag)
    if mag >= 4.0: return {"status": "RİSKLİ", "color": "#ff4444"}
    elif mag >= 3.0: return {"status": "ORTA", "color": "#ffbb33"}
    else: return {"status": "GÜVENLİ", "color": "#00C851"}

@app.route('/')
def index():
    return render_template_string(HTML_SABLONU)

@app.route('/test')
def test_mesaji():
    mag = round(random.uniform(3.0, 4.5), 1)
    risk = sismik_risk_etiketi(mag, 10)
    mesaj = f"🚀 <b>PANEL BAĞLANTI TESTİ</b>\\n\\n📊 Büyüklük: {mag}\\n🚦 Durum: {risk['status']}\\n✅ Ana sayfa ve bot şu an aktif!"
    telegram_gonder(mesaj)
    return "✅ Test mesajı gönderildi. Ana sayfayı kontrol et: <a href='/'>Buraya Tıkla</a>"

@app.route('/get_data')
def get_data():
    try:
        api_res = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live", timeout=8)
        api_data = api_res.json()
        
        # Kandilli'den gerçek saatleri çekme
        k_res = requests.get("http://www.koeri.boun.edu.tr/scripts/lst6.asp", timeout=8)
        k_res.encoding = 'utf-8'
        soup = BeautifulSoup(k_res.text, 'html.parser')
        ham_saatler = re.findall(r'(\d{2}:\d{2}:\d{2})', soup.find('pre').text)

        if api_data.get("result"):
            # Yeni Deprem Bildirimi
            ilk = api_data["result"][0]
            if ilk["earthquake_id"] != LAST_NOTIFIED_ID[0]:
                mag = float(ilk["mag"])
                if mag >= 1.5:
                    risk = sismik_risk_etiketi(mag, ilk["depth"])
                    saat = ham_saatler[0] if ham_saatler else "---"
                    m = f"🔔 <b>YENİ DEPREM</b>\\n\\n📍 Yer: {ilk['title']}\\n📊 Büyüklük: <b>{mag}</b>\\n⏰ Saat: {saat}\\n🚦 Analiz: {risk['status']}"
                    telegram_gonder(m)
                LAST_NOTIFIED_ID[0] = ilk["earthquake_id"]

            # Panel için verileri zenginleştir
            for i in range(len(api_data["result"])):
                q = api_data["result"][i]
                q["custom_hour"] = ham_saatler[i] if i < len(ham_saatler) else "00:00"
                q["risk_analysis"] = sismik_risk_etiketi(q["mag"], q["depth"])
                
        return jsonify(api_data)
    except Exception as e:
        return jsonify({"result": [], "error": str(e)})

if __name__ == '__main__':
    app.run(debug=True)

