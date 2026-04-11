from flask import Flask, jsonify, render_template_string, request
import requests

app = Flask(__name__)

# --- GÜNCEL AYARLAR ---
# Yeni Token ve Doğru Chat ID
TELEGRAM_TOKEN = "8661340862:AAF2F7wpAvuFsH1xAtaYWBi-A0mG6ZiYPsY"
CHAT_ID = "-1003826426476" 
LAST_NOTIFIED_ID = [None]

# ANA SAYFA TASARIMI
HTML_SABLONU = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sismik Risk Analiz Paneli</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #0f172a; color: white; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        header { background: #1e293b; padding: 12px 20px; border-bottom: 2px solid #334155; display: flex; justify-content: space-between; align-items: center; }
        .main-container { display: flex; flex: 1; overflow: hidden; }
        #map { flex: 2; height: 100%; border-right: 1px solid #334155; z-index: 1; }
        .sidebar { flex: 0.8; background: #111827; overflow-y: auto; padding: 10px; display: flex; flex-direction: column; gap: 8px; }
        .quake-card { background: #1f2937; padding: 12px; border-radius: 8px; border-left: 5px solid #3b82f6; cursor: pointer; transition: 0.2s; position: relative; }
        .mag { font-size: 1.4rem; font-weight: bold; color: #10b981; }
        .loc { font-size: 0.85rem; font-weight: 600; color: #e2e8f0; }
        .time { font-size: 0.75rem; color: #94a3b8; margin-top: 4px; }
        @media (max-width: 768px) { .main-container { flex-direction: column; } #map { flex: none; height: 40%; } .sidebar { flex: 1; } }
    </style>
</head>
<body>
    <header>
        <div>📡 <b>SİSMİK RİSK ANALİZ PANELİ</b></div>
        <div id="clock" style="color: #60a5fa; font-family: monospace;">00:00:00</div>
    </header>
    <div class="main-container">
        <div id="map"></div>
        <div class="sidebar" id="liste">Veriler yükleniyor...</div>
    </div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        setInterval(() => { document.getElementById('clock').innerText = new Date().toLocaleTimeString('tr-TR'); }, 1000);
        let map = L.map('map', {zoomControl: false}).setView([39.0, 35.0], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        let marker = L.marker([39.0, 35.0]).addTo(map);

        async function updateData() {
            try {
                const res = await fetch('/get_data');
                const data = await res.json();
                let html = "";
                data.result.slice(0, 35).forEach((q) => {
                    const coords = q.geojson.coordinates;
                    html += `<div class="quake-card" onclick="map.setView([${coords[1]},${coords[0]}],10); marker.setLatLng([${coords[1]},${coords[0]}]).bindPopup('${q.title}').openPopup();">
                        <div class="mag">${q.mag}</div>
                        <div class="loc">${q.title}</div>
                        <div class="time">Saat: ${q.date_time.split(' ')[1]}</div>
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
        requests.post(url, data=payload, timeout=8)
    except: pass

@app.route('/')
def index():
    return render_template_string(HTML_SABLONU)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        if "message" in update and "text" in update["message"]:
            msg = update["message"]["text"].lower()
            if "/test" in msg:
                telegram_gonder("✅ <b>SİSTEM AKTİF!</b>\\nPanel ve Telegram bağlantısı sorunsuz çalışıyor.")
    except: pass
    return "OK", 200

@app.route('/get_data')
def get_data():
    try:
        api_res = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live", timeout=8).json()
        if api_res.get("result"):
            ilk = api_res["result"][0]
            if ilk["earthquake_id"] != LAST_NOTIFIED_ID[0]:
                if float(ilk["mag"]) >= 1.5:
                    telegram_gonder(f"🔔 <b>YENİ DEPREM</b>\\n📍 Yer: {ilk['title']}\\n📊 Büyüklük: {ilk['mag']}")
                LAST_NOTIFIED_ID[0] = ilk["earthquake_id"]
        return jsonify(api_res)
    except: return jsonify({"result": []})

if __name__ == '__main__':
    app.run()
