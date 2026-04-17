from flask import Flask, jsonify, render_template_string, request, make_response
import requests

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = "8661340862:AAF2F7wpAvuFsH1xAtaYWBi-A0mG6ZiYPsY"
CHAT_ID = "-1003273342330"
LAST_NOTIFIED_ID = [None]

# GÜNCEL TASARIM (APK UYUMLU)
HTML_SABLONU = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Sismik Risk Paneli</title>
    
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#1e293b">
    <meta name="mobile-web-app-capable" content="yes">
    
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #0b1120; color: white; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        header { background: #1e293b; padding: 10px 15px; border-bottom: 2px solid #334155; display: flex; justify-content: space-between; align-items: center; z-index: 1000; }
        .main-container { display: flex; flex: 1; overflow: hidden; }
        #map { flex: 2; height: 100%; border-right: 1px solid #334155; z-index: 1; background: #0b1120; }
        .sidebar { flex: 0.8; background: #111827; overflow-y: auto; padding: 10px; display: flex; flex-direction: column; gap: 8px; }
        .quake-card { background: #1f2937; padding: 12px; border-radius: 8px; border-left: 5px solid #10b981; cursor: pointer; position: relative; }
        .status-badge { position: absolute; top: 10px; right: 10px; font-size: 0.6rem; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
        .mag { font-size: 1.4rem; font-weight: bold; }
        .loc { font-size: 0.85rem; font-weight: 600; text-transform: uppercase; margin: 3px 0; }
        .details { font-size: 0.75rem; color: #94a3b8; display: flex; justify-content: space-between; }
        @media (max-width: 768px) { .main-container { flex-direction: column; } #map { flex: none; height: 45%; } .sidebar { flex: 1; } }
    </style>
</head>
<body>
    <header>
        <div>📡 <b>SİSMİK PANEL</b></div>
        <div id="clock" style="color:#60a5fa; font-family:monospace;">00:00:00</div>
    </header>
    <div class="main-container">
        <div id="map"></div>
        <div class="sidebar" id="liste">Yükleniyor...</div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        setInterval(() => { document.getElementById('clock').innerText = new Date().toLocaleTimeString('tr-TR'); }, 1000);
        
        // Harita ve Marker Ayarları
        var map = L.map('map', {zoomControl: false}).setView([39.0, 35.2], 5);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; OSM'
        }).addTo(map);
        
        var marker = L.marker([39.0, 35.0]).addTo(map);

        async function updateData() {
            try {
                const res = await fetch('/get_data');
                const data = await res.json();
                let html = "";
                data.result.slice(0, 30).forEach((q) => {
                    const coords = q.geojson.coordinates;
                    const mag = parseFloat(q.mag);
                    let color = "#10b981"; let label = "🟢 GÜVENLİ";
                    if(mag >= 4.0) { color = "#ef4444"; label = "🔴 RİSKLİ"; }
                    else if(mag >= 3.0) { color = "#f59e0b"; label = "🟡 ORTA"; }

                    html += `<div class="quake-card" style="border-left-color: ${color}" onclick="focusMap(${coords[1]},${coords[0]},'${q.title}')">
                        <div class="status-badge" style="color:${color}; border: 1px solid ${color}">${label}</div>
                        <div class="mag" style="color:${color}">${q.mag}</div>
                        <div class="loc">${q.title}</div>
                        <div class="details"><span>🕒 ${q.date_time.split(' ')[1]}</span><span>📏 ${q.depth} km</span></div>
                    </div>`;
                });
                document.getElementById('liste').innerHTML = html;
            } catch(e) { document.getElementById('liste').innerHTML = "Bağlantı Hatası!"; }
        }

        function focusMap(lat, lng, title) {
            map.setView([lat, lng], 8);
            marker.setLatLng([lat, lng]).bindPopup(title).openPopup();
        }

        updateData(); setInterval(updateData, 30000);
        
        // Service Worker Kaydı
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/sw.js');
        }
    </script>
</body>
</html>
"""

# --- YENİ ROTALAR (APK HATALARINI ÇÖZER) ---

@app.route('/manifest.json')
def manifest():
    return jsonify({
        "short_name": "SismikPanel",
        "name": "Sismik Risk Analiz Paneli",
        "icons": [{"src": "https://cdn-icons-png.flaticon.com/512/2554/2554930.png", "sizes": "512x512", "type": "image/png"}],
        "start_url": "/",
        "display": "standalone",
        "theme_color": "#1e293b",
        "background_color": "#0b1120"
    })

@app.route('/sw.js')
def sw():
    response = make_response("self.addEventListener('fetch', function(event) {});")
    response.headers['Content-Type'] = 'application/javascript'
    return response

@app.route('/')
def index(): return render_template_string(HTML_SABLONU)

@app.route('/get_data')
def get_data():
    try:
        r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live", timeout=8).json()
        if r.get("result"):
            son = r["result"][0]
            if son["earthquake_id"] != LAST_NOTIFIED_ID[0]:
                if float(son["mag"]) >= 1.5:
                    tg_post(f"🔔 <b>YENİ DEPREM</b>\\n📊 {son['mag']} | {son['title']}\\n📏 {son['depth']} km")
                LAST_NOTIFIED_ID[0] = son["earthquake_id"]
        return jsonify(r)
    except: return jsonify({"result": []})

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        upd = request.get_json()
        if "message" in upd and "text" in upd["message"]:
            msg = upd["message"]["text"].lower()
            if "/deprem" in msg:
                r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live").json()
                if r.get("result"):
                    s = r["result"][0]
                    tg_post(f"📢 <b>SON DEPREM</b>\\n📊 {s['mag']}\\n📍 {s['title']}\\n⏰ {s['date_time']}")
            elif "/liste" in msg:
                r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live").json()
                if r.get("result"):
                    txt = "📋 <b>SON 10 DEPREM</b>\\n"
                    for q in r["result"][:10]:
                        txt += f"▪️ <b>{q['mag']}</b> | {q['title']}\\n"
                    tg_post(txt)
    except: pass
    return "OK", 200

def tg_post(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text.replace("\\n", "\n"), "parse_mode": "HTML"}, timeout=5)

if __name__ == '__main__': app.run()
