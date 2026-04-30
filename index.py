from flask import Flask, jsonify, render_template_string, request
import requests

app = Flask(__name__)

# --- AYARLAR ---
# GÜVENLİK NOTU: Bu tokenı BotFather'dan yenilemeni şiddetle öneririm!
TELEGRAM_TOKEN = "8661340862:AAFAsuLeneLik60CI9DEVwpdQ8KjWI_OBDc"
CHAT_ID = "-1003273342330"
COLLECT_API_KEY = "apikey 5GIip3rMo8hha15ETPnLnt:4TkrPv1j9K1AzvUl0pYLUK"

# Bellekte tutulan veriler (Vercel'de uygulama uyuduğunda bunlar sıfırlanabilir)
LAST_NOTIFIED_ID = [None]
TRACKED_MATCHES = {}

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
        .status-badge { position: absolute; top: 10px; right: 10px; font-size: 0.6rem; padding: 2px 6px; border-radius: 4px; font-weight: bold; border: 1px solid; }
        .mag { font-size: 1.4rem; font-weight: bold; }
        .loc { font-size: 0.85rem; font-weight: 600; color: #e2e8f0; margin: 3px 0; text-transform: uppercase; }
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
                        <div class="status-badge" style="color:${color}; border-color:${color}">${label}</div>
                        <div class="mag" style="color:${color}">${q.mag}</div>
                        <div class="loc">${q.title}</div>
                        <div class="details"><span>🕒 ${q.date_time.split(' ')[1]}</span><span>📏 Derinlik: ${q.depth} km</span></div>
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

def tg_post(text, target_id=None):
    if target_id is None: target_id = CHAT_ID
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": target_id, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=5)
    except:
        pass

def get_risk_info(mag):
    m = float(mag)
    if m >= 4.0: return "🔴 RİSKLİ"
    if m >= 3.0: return "🟡 ORTA"
    return "🟢 GÜVENLİ"

def get_collect_match(search_term):
    headers = {'content-type': "application/json", 'authorization': COLLECT_API_KEY}
    try:
        url = "https://api.collectapi.com/football/results?league=super-lig"
        res = requests.get(url, headers=headers, timeout=8).json()
        if res.get("success"):
            for match in res["result"]:
                if search_term.lower() in match['home'].lower() or search_term.lower() in match['away'].lower():
                    return match
    except: return None
    return None

@app.route('/')
def index():
    return render_template_string(HTML_SABLONU)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        upd = request.get_json()
        if not upd or "message" not in upd:
            return "OK", 200
            
        msg = upd["message"].get("text", "").lower()
        sender_id = upd["message"]["chat"]["id"]

        # Komut İşleme
        if "/start" in msg:
            tg_post("Sistem Aktif! /deprem veya /liste yazabilirsin.", sender_id)

        elif "/deprem" in msg:
            r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live").json()
            s = r["result"][0]
            text = f"📢 <b>SON DEPREM</b>\n\n📊 <b>Büyüklük:</b> {s['mag']} ({get_risk_info(s['mag'])})\n📍 <b>Yer:</b> {s['title']}\n📏 <b>Derinlik:</b> {s['depth']} km\n⏰ <b>Saat:</b> {s['date_time']}"
            tg_post(text, sender_id)

        elif "/liste" in msg:
            r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live").json()
            text = "📋 <b>SON 10 DEPREM</b>\n───────────────────\n"
            for q in r["result"][:10]:
                text += f"▪️ <b>{q['mag']}</b> | {q['title']}\n    └ {get_risk_info(q['mag'])} | 🕒 {q['date_time'].split(' ')[1]}\n\n"
            tg_post(text, sender_id)

        elif msg.startswith("/ac"):
            term = msg.replace("/ac", "").strip()
            match = get_collect_match(term)
            if match:
                TRACKED_MATCHES[term] = {"last_score": match['skor']}
                text = f"🏟️ <b>TAKİP BAŞLADI:</b> {match['home']} vs {match['away']}\n🥅 <b>Skor:</b> {match['skor']}"
                tg_post(text, sender_id)
            else:
                tg_post(f"❌ {term.upper()} için maç bulunamadı.", sender_id)

    except Exception as e:
        print(f"Hata: {e}")
    
    return "OK", 200

@app.route('/get_data')
def get_data():
    r_data = {"result": []}
    try:
        r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live", timeout=8).json()
        if r.get("result"):
            r_data = r
            son = r["result"][0]
            # Sadece büyük depremlerde otomatik gruba mesaj at
            if son["earthquake_id"] != LAST_NOTIFIED_ID[0]:
                if float(son["mag"]) >= 3.0:
                    tg_post(f"🔔 <b>OTOMATİK BİLDİRİM</b>\n\n📊 {son['mag']} | {son['title']}")
                LAST_NOTIFIED_ID[0] = son["earthquake_id"]
    except: pass
    return jsonify(r_data)

# Vercel için gerekli
if __name__ == '__main__':
    app.run(debug=True)
