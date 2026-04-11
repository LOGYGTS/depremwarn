from flask import Flask, jsonify, render_template_string, request
import requests

app = Flask(__name__)

# --- AYARLAR (BURAYI KONTROL ET) ---
# Token başında veya sonunda boşluk kalmadığından emin ol
TELEGRAM_TOKEN = "8661340862:AAF23SAF8bVEMx7lBXBdyEfqRelLMENIs3s"
# Chat ID'nin başındaki eksi (-) işaretini unutma
CHAT_ID = "-1005272137007" 

LAST_NOTIFIED_ID = [None]

# Harita Paneli Tasarımı
HTML_SABLONU = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Sismik Risk Paneli</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { font-family: sans-serif; margin: 0; background: #0f172a; color: white; }
        header { background: #1e293b; padding: 15px; border-bottom: 3px solid #3b82f6; text-align: center; }
        .dashboard { display: flex; height: calc(100vh - 65px); }
        #map { flex: 2; background: #334155; }
        .sidebar { flex: 1; background: #1e293b; overflow-y: auto; padding: 10px; }
        .card { background: #334155; padding: 12px; margin-bottom: 8px; border-radius: 6px; border-left: 5px solid #3b82f6; }
    </style>
</head>
<body>
    <header><h3>📡 SİSMİK RİSK ANALİZİ</h3></header>
    <div class="dashboard"><div id="map"></div><div class="sidebar" id="liste">Yükleniyor...</div></div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        let map = L.map('map').setView([39.0, 35.0], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        let marker = L.marker([39.0, 35.0]).addTo(map);

        async function updateData() {
            try {
                const res = await fetch('/get_data');
                const data = await res.json();
                let html = "";
                data.result.slice(0, 20).forEach((q) => {
                    const coords = q.geojson.coordinates;
                    html += `<div class="card" onclick="map.setView([${coords[1]},${coords[0]}],10); marker.setLatLng([${coords[1]},${coords[0]}]).bindPopup('${q.title}').openPopup();">
                        <b>${q.mag}</b> - ${q.title}
                    </div>`;
                });
                document.getElementById('liste').innerHTML = html;
            } catch(e) { console.error("Veri hatası:", e); }
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
        r = requests.post(url, data=payload, timeout=5)
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.route('/')
def index():
    return render_template_string(HTML_SABLONU)

@app.route('/webhook', methods=['POST'])
def webhook():
    update = request.get_json()
    if "message" in update and "text" in update["message"]:
        if "/test" in update["message"]["text"]:
            telegram_gonder("🚀 <b>Sistem Aktif!</b>\\nToken ve ID bağlantısı başarıyla sağlandı.")
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
    except:
        return jsonify({"result": []})

if __name__ == '__main__':
    app.run()
