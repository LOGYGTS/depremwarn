from flask import Flask, jsonify, render_template_string, request
import requests

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = "8661340862:AAF2F7wpAvuFsH1xAtaYWBi-A0mG6ZiYPsY"
CHAT_ID = "-1003273342330"
LAST_NOTIFIED_ID = [None]
TRACKED_MATCHES = {} # { "takim_adi": {"last_score": "0-0", "is_notified": False} }

# --- WEB PANEL TASARIMI ---
HTML_SABLONU = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sismik & Skor Analiz Paneli</title>
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
        .details { font-size: 0.75rem; color: #94a3b8; display: flex; justify-content: space-between; }
    </style>
</head>
<body>
    <header>
        <div>📡 <b>SİSMİK & SKOR ANALİZ PANELİ</b></div>
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
                    let color = (mag >= 4.0) ? "#ef4444" : (mag >= 3.0 ? "#f59e0b" : "#10b981");
                    html += `<div class="quake-card" style="border-left-color: ${color}" onclick="map.setView([${coords[1]},${coords[0]}],8); marker.setLatLng([${coords[1]},${coords[0]}]).bindPopup('${q.title}').openPopup();"><div class="mag" style="color:${color}">${q.mag}</div><div class="loc">${q.title}</div><div class="details"><span>🕒 ${q.date_time.split(' ')[1]}</span><span>📏 ${q.depth} km</span></div></div>`;
                });
                document.getElementById('liste').innerHTML = html;
            } catch(e) {}
        }
        updateData(); setInterval(updateData, 30000);
    </script>
</body>
</html>
"""

# --- YARDIMCI FONKSİYONLAR ---
def tg_post(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=5)

def get_risk_info(mag):
    m = float(mag)
    if m >= 4.0: return "🔴 RİSKLİ"
    if m >= 3.0: return "🟡 ORTA"
    return "🟢 GÜVENLİ"

# --- FLASK YOLLARI ---
@app.route('/')
def index(): return render_template_string(HTML_SABLONU)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        upd = request.get_json()
        if "message" in upd and "text" in upd["message"]:
            msg = upd["message"]["text"].lower()
            
            # --- DEPREM KOMUTLARI ---
            if "/deprem" in msg:
                r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live").json()
                s = r["result"][0]
                text = f"📢 <b>SON DEPREM</b>\n\n📊 <b>Büyüklük:</b> {s['mag']} ({get_risk_info(s['mag'])})\n📍 <b>Yer:</b> {s['title']}\n📏 <b>Derinlik:</b> {s['depth']} km\n⏰ <b>Saat:</b> {s['date_time']}"
                tg_post(text)

            elif "/liste" in msg:
                r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live").json()
                text = "📋 <b>SON 10 DEPREM</b>\n───────────────────\n"
                for q in r["result"][:10]:
                    text += f"▪️ <b>{q['mag']}</b> | {q['title']}\n    └ {get_risk_info(q['mag'])} | 🕒 {q['date_time'].split(' ')[1]} | 📏 {q['depth']} km\n\n"
                tg_post(text)

            # --- MAÇ KOMUTLARI ---
            elif msg.startswith("/ac"):
                takim = msg.replace("/ac", "").strip()
                if takim:
                    # Tekrarı önlemek için is_notified False ile başlar
                    TRACKED_MATCHES[takim] = {"last_score": "0-0", "is_notified": False}
                    tg_post(f"⚽ <b>{takim.upper()}</b> takibe alındı. Bilgiler hazırlanıyor...")

            elif msg.startswith("/kapat"):
                takim = msg.replace("/kapat", "").strip()
                if takim in TRACKED_MATCHES:
                    del TRACKED_MATCHES[takim]
                    tg_post(f"📴 {takim.upper()} takibi durduruldu.")
    except: pass
    return "OK", 200

@app.route('/get_data')
def get_data():
    # 1. Deprem Kontrolü
    r_data = {"result": []}
    try:
        r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live", timeout=8).json()
        if r.get("result"):
            r_data = r
            son = r["result"][0]
            if son["earthquake_id"] != LAST_NOTIFIED_ID[0]:
                if float(son["mag"]) >= 1.5:
                    tg_post(f"🔔 <b>YENİ DEPREM</b>\n\n📊 {son['mag']} ({get_risk_info(son['mag'])})\n📍 {son['title']}\n📏 {son['depth']} km")
                LAST_NOTIFIED_ID[0] = son["earthquake_id"]
    except: pass
    
    # 2. Ücretsiz Maç Takibi (Tekrarı Önleyen Sistem)
    for takim in list(TRACKED_MATCHES.keys()):
        try:
            # Burası canlı veri çeker (Şu an örnek veri döner)
            skor = "0 - 0" 
            
            # İlk Bildirim (Sadece 1 kez atılır)
            if not TRACKED_MATCHES[takim]["is_notified"]:
                text = (f"🏟️ <b>MAÇ DETAYLARI: {takim.upper()}</b>\n"
                        f"───────────────────\n"
                        f"🕒 <b>Maç Saati:</b> 20:45\n"
                        f"📍 <b>Stadyum:</b> Şükrü Saracoğlu\n"
                        f"⚖️ <b>Hakem:</b> Halil Umut Meler\n"
                        f"📋 <b>Kadro:</b> <i>Canlı veriden çekiliyor...</i>\n"
                        f"───────────────────")
                tg_post(text)
                TRACKED_MATCHES[takim]["is_notified"] = True
            
            # Skor Değişirse Bildirim Atar
            if skor != TRACKED_MATCHES[takim]["last_score"]:
                tg_post(f"⚽ <b>GOOOOOOLLLL!</b>\n───────────────────\n🥅 <b>Skor:</b> {skor}")
                TRACKED_MATCHES[takim]["last_score"] = skor
        except: pass

    return jsonify(r_data)

if __name__ == '__main__':
    app.run()
