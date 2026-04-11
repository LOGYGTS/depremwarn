from flask import Flask, jsonify, render_template_string, request
import requests

app = Flask(__name__)

# --- AYARLAR ---
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
    <title>Sismik Analiz Paneli</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #0b1120; color: white; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        header { background: #1e293b; padding: 10px 20px; border-bottom: 2px solid #334155; display: flex; justify-content: space-between; align-items: center; }
        .main { display: flex; flex: 1; overflow: hidden; }
        #map { flex: 2; height: 100%; }
        .sidebar { flex: 0.8; background: #111827; overflow-y: auto; padding: 10px; border-left: 1px solid #334155; }
        .card { background: #1e293b; padding: 12px; border-radius: 8px; border-left: 4px solid #10b981; margin-bottom: 8px; cursor: pointer; transition: 0.2s; }
        .card:hover { background: #334155; }
        .mag { font-size: 1.3rem; font-weight: bold; color: #10b981; }
        @media (max-width: 768px) { .main { flex-direction: column; } #map { height: 40%; } }
    </style>
</head>
<body>
    <header><div>📡 <b>SİSMİK RİSK ANALİZ PANELİ</b></div></header>
    <div class="main">
        <div id="map"></div>
        <div class="sidebar" id="liste">Yükleniyor...</div>
    </div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Harita başlangıç zoom seviyesi Türkiye'yi tam görecek şekilde ayarlandı
        let map = L.map('map', {zoomControl: false}).setView([39.0, 35.2], 5);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        let marker = L.marker([39.0, 35.0]).addTo(map);

        async function update() {
            try {
                const res = await fetch('/get_data');
                const data = await res.json();
                let h = "";
                data.result.slice(0, 30).forEach(q => {
                    const c = q.geojson.coordinates;
                    h += `<div class="card" onclick="map.setView([${c[1]},${c[0]}],8); marker.setLatLng([${c[1]},${c[0]}]).bindPopup('${q.title}').openPopup();">
                        <div class="mag">${q.mag}</div>
                        <div style="font-size:0.9rem; font-weight:600;">${q.title}</div>
                        <div style="font-size:0.75rem; color:#94a3b8;">${q.date_time}</div>
                    </div>`;
                });
                document.getElementById('liste').innerHTML = h;
            } catch(e) {}
        }
        update(); setInterval(update, 30000);
    </script>
</body>
</html>
"""

def tg_post(text):
    clean_text = text.replace("\\n", "\n")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": clean_text, "parse_mode": "HTML"}, timeout=5)

@app.route('/')
def index(): return render_template_string(HTML_SABLONU)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        upd = request.get_json()
        if "message" in upd and "text" in upd["message"]:
            msg = upd["message"]["text"].lower()
            
            # /deprem komutu eklendi
            if "/deprem" in msg:
                r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live").json()
                if r.get("result"):
                    son = r["result"][0]
                    text = f"📢 <b>Son Deprem Bilgisi</b>\n\n📍 Yer: {son['title']}\n📊 Büyüklük: {son['mag']}\n⏰ Saat: {son['date_time']}"
                    tg_post(text)
    except: pass
    return "OK", 200

@app.route('/get_data')
def get_data():
    try:
        r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live", timeout=8).json()
        if r.get("result"):
            son = r["result"][0]
            if son["earthquake_id"] != LAST_NOTIFIED_ID[0]:
                if float(son["mag"]) >= 1.5:
                    msg = f"🔔 <b>YENİ DEPREM</b>\n📍 Yer: {son['title']}\n📊 Büyüklük: {son['mag']}"
                    tg_post(msg)
                LAST_NOTIFIED_ID[0] = son["earthquake_id"]
        return jsonify(r)
    except: return jsonify({"result": []})

if __name__ == '__main__': app.run()
