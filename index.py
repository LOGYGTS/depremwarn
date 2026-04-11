from flask import Flask, jsonify, render_template_string, request
import requests

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = "8661340862:AAF2F7wpAvuFsH1xAtaYWBi-A0mG6ZiYPsY"
CHAT_ID = "-1003826426476"
# Son bildirilen depremi hafızada tutarak mükerrer mesajı önler
LAST_NOTIFIED_ID = [None]

# ANA SAYFA TASARIMI (Split Screen & Risk Algoritması)
HTML_SABLONU = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sismik Risk Analiz Paneli</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #0b1120; color: white; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        header { background: #1e293b; padding: 10px 20px; border-bottom: 2px solid #334155; display: flex; justify-content: space-between; align-items: center; z-index: 1000; }
        .live-clock { color: #60a5fa; font-family: monospace; font-size: 1.1rem; }
        .main-container { display: flex; flex: 1; overflow: hidden; }
        #map { flex: 2; height: 100%; border-right: 1px solid #334155; z-index: 1; }
        .sidebar { flex: 0.8; background: #111827; overflow-y: auto; padding: 10px; display: flex; flex-direction: column; gap: 8px; }
        .quake-card { background: #1f2937; padding: 12px 15px; border-radius: 8px; border-left: 5px solid #10b981; cursor: pointer; transition: 0.2s; position: relative; }
        .quake-card:hover { background: #334155; transform: translateX(3px); }
        .status-badge { position: absolute; top: 10px; right: 10px; font-size: 0.6rem; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
        .mag { font-size: 1.4rem; font-weight: bold; margin-bottom: 2px; }
        .loc { font-size: 0.85rem; font-weight: 600; text-transform: uppercase; color: #e2e8f0; margin-bottom: 3px; }
        .time { font-size: 0.75rem; color: #94a3b8; }
        @media (max-width: 768px) { .main-container { flex-direction: column; } #map { flex: none; height: 40%; } .sidebar { flex: 1; } }
    </style>
</head>
<body>
    <header>
        <div>📡 <b>SİSMİK RİSK ANALİZ PANELİ</b></div>
        <div id="clock" class="live-clock">00:00:00</div>
    </header>
    <div class="main-container">
        <div id="map"></div>
        <div class="sidebar" id="liste">Veriler yükleniyor...</div>
    </div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        setInterval(() => { document.getElementById('clock').innerText = new Date().toLocaleTimeString('tr-TR'); }, 1000);
        let map = L.map('map', {zoomControl: false}).setView([39.0, 35.2], 5);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        let marker = L.marker([39.0, 35.0]).addTo(map);

        async function updateData() {
            try {
                const res = await fetch('/get_data');
                const data = await res.json();
                let html = "";
                data.result.slice(0, 35).forEach((q) => {
                    const coords = q.geojson.coordinates;
                    const mag = parseFloat(q.mag);
                    let color = "#10b981"; let label = "🟢 GÜVENLİ";
                    if(mag >= 4.0) { color = "#ef4444"; label = "🔴 RİSKLİ"; }
                    else if(mag >= 3.0) { color = "#f59e0b"; label = "🟡 ORTA"; }

                    html += `
                    <div class="quake-card" style="border-left-color: ${color}" onclick="map.setView([${coords[1]},${coords[0]}],8); marker.setLatLng([${coords[1]},${coords[0]}]).bindPopup('${q.title}').openPopup();">
                        <div class="status-badge" style="color:${color}; border: 1px solid ${color}">${label}</div>
                        <div class="mag" style="color:${color}">${q.mag}</div>
                        <div class="loc">${q.title}</div>
                        <div class="time">Saat: ${q.date_time.split(' ')[1]}</div>
                    </div>`;
                });
                document.getElementById('liste').innerHTML = html;
            } catch(e) { console.error("Hata:", e); }
        }
        updateData(); setInterval(updateData, 30000);
    </script>
</body>
</html>
"""

def get_risk_info(mag):
    m = float(mag)
    if m >= 4.0: return "🔴 RİSKLİ"
    if m >= 3.0: return "🟡 ORTA"
    return "🟢 GÜVENLİ"

def tg_post(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=5)

@app.route('/')
def index(): return render_template_string(HTML_SABLONU)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        upd = request.get_json()
        if "message" in upd and "text" in upd["message"]:
            msg_text = upd["message"]["text"].lower()
            if "/deprem" in msg_text:
                r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live").json()
                if r.get("result"):
                    son = r["result"][0]
                    risk = get_risk_info(son['mag'])
                    text = (f"📡 <b>SON DEPREM</b>\\n\\n"
                            f"📊 <b>Büyüklük:</b> {son['mag']} ({risk})\\n"
                            f"📍 <b>Yer:</b> {son['title']}\\n"
                            f"⏰ <b>Saat:</b> {son['date_time']}")
                    tg_post(text.replace("\\n", "\n"))
    except: pass
    return "OK", 200

@app.route('/get_data')
def get_data():
    try:
        r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live", timeout=8).json()
        if r.get("result"):
            son = r["result"][0]
            # SİSTEMİN KALBİ: Yeni bir deprem ID'si gelirse otomatik atar
            if son["earthquake_id"] != LAST_NOTIFIED_ID[0]:
                if float(son["mag"]) >= 1.5:
                    risk = get_risk_info(son['mag'])
                    msg = (f"🔔 <b>OTOMATİK BİLDİRİM</b>\\n\\n"
                           f"📊 <b>Büyüklük:</b> {son['mag']} ({risk})\\n"
                           f"📍 <b>Yer:</b> {son['title']}\\n"
                           f"⏰ <b>Saat:</b> {son['date_time'].split(' ')[1]}")
                    tg_post(msg.replace("\\n", "\n"))
                LAST_NOTIFIED_ID[0] = son["earthquake_id"]
        return jsonify(r)
    except: return jsonify({"result": []})

if __name__ == '__main__': app.run()
