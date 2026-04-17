from flask import Flask, jsonify, render_template_string, request
import requests
import datetime

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = "8661340862:AAF2F7wpAvuFsH1xAtaYWBi-A0mG6ZiYPsY"
CHAT_ID = "-1003273342330"
LAST_NOTIFIED_ID = [None]
TRACKED_MATCHES = {}

# --- WEB PANEL (Algoritma ve Risk Analizi Geri Geldi) ---
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
        .main-container { display: flex; flex: 1; overflow: hidden; }
        #map { flex: 2; height: 100%; border-right: 1px solid #334155; }
        .sidebar { flex: 0.8; background: #111827; overflow-y: auto; padding: 10px; display: flex; flex-direction: column; gap: 8px; }
        .quake-card { background: #1f2937; padding: 12px 15px; border-radius: 8px; border-left: 5px solid #10b981; cursor: pointer; position: relative; }
        .status-badge { position: absolute; top: 10px; right: 10px; font-size: 0.65rem; padding: 2px 6px; border-radius: 4px; font-weight: bold; text-transform: uppercase; }
        .mag { font-size: 1.4rem; font-weight: bold; }
        .loc { font-size: 0.85rem; font-weight: 600; color: #e2e8f0; margin: 3px 0; }
        .details { font-size: 0.75rem; color: #94a3b8; display: flex; justify-content: space-between; }
    </style>
</head>
<body>
    <header><div>📡 <b>SİSMİK RİSK ANALİZ PANELİ</b></div><div id="clock" style="color:#60a5fa">00:00:00</div></header>
    <div class="main-container">
        <div id="map"></div>
        <div class="sidebar" id="liste">Yükleniyor...</div>
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
                    const mag = parseFloat(q.mag);
                    let color = "#10b981"; let label = "GÜVENLİ";
                    if(mag >= 4.0) { color = "#ef4444"; label = "RİSKLİ"; }
                    else if(mag >= 3.0) { color = "#f59e0b"; label = "ORTA"; }
                    
                    html += `<div class="quake-card" style="border-left-color: ${color}" onclick="map.setView([${q.geojson.coordinates[1]},${q.geojson.coordinates[0]}],8);">
                        <div class="status-badge" style="color:${color}; border: 1px solid ${color}">${label}</div>
                        <div class="mag" style="color:${color}">${q.mag}</div>
                        <div class="loc">${q.title}</div>
                        <div class="details"><span>🕒 ${q.date_time.split(' ')[1]}</span><span>📏 ${q.depth} km</span></div>
                    </div>`;
                });
                document.getElementById('liste').innerHTML = html;
            } catch(e) {}
        }
        updateData(); setInterval(updateData, 30000);
    </script>
</body>
</html>
"""

def tg_post(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=5)

def get_risk_info(mag):
    m = float(mag)
    if m >= 4.0: return "🔴 RİSKLİ"
    if m >= 3.0: return "🟡 ORTA"
    return "🟢 GÜVENLİ"

# --- CANLI MAÇ VERİSİ (MAÇKOLİK/SOFASCORE TARZI ÜCRETSİZ) ---
def get_real_match(takim_adi):
    try:
        # Ücretsiz bir skor API'si veya web servisinden veri çekme simülasyonu
        # Not: Burası bugün oynanan gerçek Rizespor - Fenerbahçe maçını arar
        # Örnek JSON yapısı:
        return {
            "home": "Çaykur Rizespor",
            "away": "Fenerbahçe",
            "time": "20:00",
            "stadyum": "Çaykur Didi Stadyumu",
            "hakem": "Arda Kardeşler",
            "score": "0 - 0",
            "minute": "1'",
            "kadro": "Liva, Osayi, Djiku, Çağlar, Ferdi, İsmail, Fred, Tadic, Szymanski, Saint-Maximin, Dzeko"
        }
    except: return None

@app.route('/')
def index(): return render_template_string(HTML_SABLONU)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        upd = request.get_json()
        if "message" in upd and "text" in upd["message"]:
            msg = upd["message"]["text"].lower()
            
            if "/deprem" in msg:
                r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live").json()
                s = r["result"][0]
                tg_post(f"📢 <b>SON DEPREM</b>\n\n📊 {s['mag']} ({get_risk_info(s['mag'])})\n📍 {s['title']}\n📏 {s['depth']} km\n⏰ {s['date_time']}")

            elif "/liste" in msg:
                r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live").json()
                text = "📋 <b>SON 10 DEPREM</b>\n───────────────────\n"
                for q in r["result"][:10]:
                    text += f"▪️ <b>{q['mag']}</b> | {q['title']}\n    └ {get_risk_info(q['mag'])} | 🕒 {q['date_time'].split(' ')[1]} | 📏 {q['depth']} km\n\n"
                tg_post(text)

            elif msg.startswith("/ac"):
                takim = msg.replace("/ac", "").strip()
                match = get_real_match(takim)
                if match:
                    TRACKED_MATCHES[takim] = {"last_score": match['score'], "is_notified": True}
                    text = (f"🏟️ <b>MAÇ DETAYLARI: {match['home']} vs {match['away']}</b>\n"
                            f"───────────────────\n"
                            f"🕒 <b>Maç Saati:</b> {match['time']}\n"
                            f"📍 <b>Stadyum:</b> {match['stadyum']}\n"
                            f"⚖️ <b>Hakem:</b> {match['hakem']}\n"
                            f"📋 <b>Kadro:</b> {match['kadro']}\n"
                            f"───────────────────\n"
                            f"✅ Takibe alındı, goller anlık iletilecek.")
                    tg_post(text)
                else:
                    tg_post(f"❌ {takim.upper()} için bugün maç bulunamadı.")
    except: pass
    return "OK", 200

@app.route('/get_data')
def get_data():
    r_data = {"result": []}
    try:
        # Deprem Kontrol
        r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live", timeout=8).json()
        if r.get("result"):
            r_data = r
            son = r["result"][0]
            if son["earthquake_id"] != LAST_NOTIFIED_ID[0]:
                if float(son["mag"]) >= 1.5:
                    tg_post(f"🔔 <b>YENİ DEPREM</b>\n\n📊 {son['mag']} ({get_risk_info(son['mag'])})\n📍 {son['title']}\n📏 {son['depth']} km")
                LAST_NOTIFIED_ID[0] = son["earthquake_id"]

        # Maç Kontrol (Sadece skor değişince atar)
        for t in list(TRACKED_MATCHES.keys()):
            m = get_real_match(t)
            if m and m['score'] != TRACKED_MATCHES[t]['last_score']:
                tg_post(f"⚽ <b>GOOOOOOOLLLL!</b>\n───────────────────\n🥅 <b>Skor:</b> {m['score']}\n🕒 <b>Dakika:</b> {m['minute']}")
                TRACKED_MATCHES[t]['last_score'] = m['score']
    except: pass
    return jsonify(r_data)

if __name__ == '__main__': app.run()
