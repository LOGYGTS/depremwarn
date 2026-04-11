from flask import Flask, jsonify, render_template_string, request
import requests

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = "8661340862:AAF23SAF8bVEMx7lBXBdyEfqRelLMENIs3s"
CHAT_ID = "-1005272137007" 
LAST_NOTIFIED_ID = [None]

# ANA SİTE TASARIMI (Görseldeki düzenin aynısı)
HTML_SABLONU = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sismik Risk Analiz Paneli</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { font-family: 'Inter', sans-serif; margin: 0; background: #0f172a; color: white; overflow: hidden; }
        header { background: #1e293b; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #334155; }
        .live-timer { color: #60a5fa; font-family: monospace; font-size: 1.1rem; }
        .dashboard { display: flex; height: calc(100vh - 60px); }
        #map { flex: 2; height: 100%; z-index: 1; }
        .sidebar { flex: 0.8; background: #111827; overflow-y: auto; padding: 10px; border-left: 1px solid #334155; }
        .quake-card { background: #1f2937; margin-bottom: 10px; padding: 15px; border-radius: 8px; border-left: 4px solid #3b82f6; cursor: pointer; transition: 0.3s; position: relative; }
        .quake-card:hover { background: #374151; }
        .mag-value { font-size: 1.5rem; font-weight: bold; margin-bottom: 4px; }
        .location { font-size: 0.85rem; color: #cbd5e1; text-transform: uppercase; }
        .time-tag { font-size: 0.75rem; color: #94a3b8; margin-top: 5px; }
        .status-badge { position: absolute; top: 10px; right: 10px; font-size: 0.65rem; padding: 2px 8px; border-radius: 10px; background: rgba(16, 185, 129, 0.1); color: #10b981; border: 1px solid #10b981; }
        @media (max-width: 768px) { .dashboard { flex-direction: column; } #map { flex: none; height: 40%; } .sidebar { flex: 1; } }
    </style>
</head>
<body>
    <header>
        <div style="display:flex; align-items:center; gap:10px;">📡 <b>SİSMİK RİSK ANALİZ PANELİ</b></div>
        <div id="clock" class="live-timer">00:00:00</div>
    </header>
    <div class="dashboard">
        <div id="map"></div>
        <div class="sidebar" id="liste">Veriler yükleniyor...</div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Saat Güncelleme
        setInterval(() => { document.getElementById('clock').innerText = new Date().toLocaleTimeString('tr-TR'); }, 1000);

        // Harita Kurulumu
        let map = L.map('map', {zoomControl: false}).setView([39.0, 35.0], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        L.control.zoom({position: 'topleft'}).addTo(map);
        let marker = L.marker([39.0, 35.0]).addTo(map);

        async function updateData() {
            try {
                const res = await fetch('/get_data');
                const data = await res.json();
                let html = "";
                data.result.slice(0, 40).forEach((q) => {
                    const coords = q.geojson.coordinates;
                    const mag = parseFloat(q.mag);
                    let color = "#10b981"; // Güvenli
                    let label = "GÜVENLİ";
                    if(mag >= 4.0) { color = "#ef4444"; label = "RİSKLİ"; }
                    else if(mag >= 3.0) { color = "#f59e0b"; label = "ORTA"; }

                    html += `
                    <div class="quake-card" style="border-left-color: ${color}" onclick="focusMap(${coords[1]}, ${coords[0]}, '${q.title}')">
                        <div class="status-badge" style="color:${color}; border-color:${color}">${label}</div>
                        <div class="mag-value">${q.mag}</div>
                        <div class="location">${q.title}</div>
                        <div class="time-tag">Saat: ${q.date_time.split(' ')[1]}</div>
                    </div>`;
                });
                document.getElementById('liste').innerHTML = html;
            } catch(e) { console.error(e); }
        }

        function focusMap(lat, lng, title) {
            map.setView([lat, lng], 10);
            marker.setLatLng([lat, lng]).bindPopup(title).openPopup();
            if(window.innerWidth <= 768) document.getElementById('map').scrollIntoView();
        }

        updateData(); setInterval(updateData, 30000);
    </script>
</body>
</html>
"""

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"}
    try: requests.post(url, data=payload, timeout=5)
    except: pass

@app.route('/')
def index():
    return render_template_string(HTML_SABLONU)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        if "message" in update and "text" in update["message"]:
            if "/test" in update["message"]["text"]:
                api_res = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live", timeout=8).json()
                if api_res.get("result"):
                    son = api_res["result"][0]
                    m = f"🚀 <b>PANEL TESTİ BAŞARILI</b>\\n\\n📍 Son Deprem: {son['title']}\\n📊 Büyüklük: {son['mag']}\\n✅ Tasarım ve Webhook Aktif!"
                    telegram_gonder(m)
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
                    telegram_gonder(f"🔔 <b>YENİ DEPREM</b>\\n\\n📍 Yer: {ilk['title']}\\n📊 Büyüklük: {ilk['mag']}")
                LAST_NOTIFIED_ID[0] = ilk["earthquake_id"]
        return jsonify(api_res)
    except: return jsonify({"result": []})

if __name__ == '__main__':
    app.run()
