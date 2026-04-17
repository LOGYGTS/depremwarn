from flask import Flask, jsonify, render_template_string, request
import requests

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = "8661340862:AAF2F7wpAvuFsH1xAtaYWBi-A0mG6ZiYPsY"
CHAT_ID = "-1003273342330"
FOOTBALL_API_KEY = "BURAYA_RAPIDAPI_KEY_GELECEK" # RapidAPI API-Football Key
LAST_NOTIFIED_ID = [None]
TRACKED_MATCHES = {} 

# HTML TASARIMI (Aynen Korundu)
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
        .details { font-size: 0.75rem; color: #94a3b8; display: flex; justify-content: space-between; }
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
                    html += `<div class="quake-card" style="border-left-color: ${color}" onclick="map.setView([${coords[1]},${coords[0]}],8); marker.setLatLng([${coords[1]},${coords[0]}]).bindPopup('${q.title}').openPopup();">
                        <div class="status-badge" style="color:${color}; border: 1px solid ${color}">${label}</div>
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

def tg_post(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=5)

def get_risk_info(mag):
    m = float(mag)
    if m >= 4.0: return "🔴 RİSKLİ"
    if m >= 3.0: return "🟡 ORTA"
    return "🟢 GÜVENLİ"

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
                son = r["result"][0]
                text = f"📢 <b>SON DEPREM BİLGİSİ</b>\n\n📊 <b>Büyüklük:</b> {son['mag']} ({get_risk_info(son['mag'])})\n📍 <b>Yer:</b> {son['title']}\n📏 <b>Derinlik:</b> {son['depth']} km\n⏰ <b>Saat:</b> {son['date_time']}"
                tg_post(text)

            elif "/liste" in msg:
                r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live").json()
                son_on = r["result"][:10]
                text = "📋 <b>SON 10 DEPREM (GÜNCEL)</b>\n───────────────────\n"
                for q in son_on:
                    text += f"▪️ <b>{q['mag']}</b> | {q['title']}\n   └ {get_risk_info(q['mag'])} | 🕒 {q['date_time'].split(' ')[1]}\n\n"
                text += "───────────────────"
                tg_post(text)

            # --- GOL VE MAÇ TAKİP KOMUTU ---
            elif msg.startswith("/ac"):
                takim = msg.replace("/ac", "").strip()
                if takim:
                    headers = {'x-rapidapi-key': FOOTBALL_API_KEY, 'x-rapidapi-host': "v3.football.api-sports.io"}
                    url = f"https://v3.football.api-sports.io/fixtures?live=all&search={takim}"
                    # Canlı maç yoksa bugünkü maçlara bak
                    res = requests.get(url, headers=headers).json()
                    if not res.get("response"):
                         url = f"https://v3.football.api-sports.io/fixtures?date=2026-04-17&search={takim}" # Güncel tarih otomatiğe bağlanabilir
                         res = requests.get(url, headers=headers).json()

                    if res.get("response"):
                        m = res["response"][0]
                        stadyum = m['fixture']['venue']['name']
                        hakem = m['fixture']['referee'] if m['fixture']['referee'] else "Belli değil"
                        saat = m['fixture']['date'].split('T')[1][:5]
                        
                        text = (f"🏟️ <b>MAÇ ANALİZİ: {m['teams']['home']['name']} vs {m['teams']['away']['name']}</b>\n"
                                f"───────────────────\n"
                                f"🕒 <b>Başlangıç:</b> {saat}\n"
                                f"📍 <b>Stadyum:</b> {stadyum}\n"
                                f"⚖️ <b>Hakem:</b> {hakem}\n")

                        # 11'ler Kontrolü
                        lineup_url = f"https://v3.football.api-sports.io/fixtures/lineups?fixture={m['fixture']['id']}"
                        l_res = requests.get(lineup_url, headers=headers).json()
                        if l_res.get("response"):
                            text += "\n📋 <b>İLK 11'LER BELLİ OLDU!</b>\n"
                            for side in l_res["response"]:
                                team_name = side['team']['name']
                                players = ", ".join([p['player']['name'] for p in side['startXI']])
                                text += f"\n👉 <b>{team_name}:</b> {players}\n"
                        else:
                            text += "\n⏳ <i>İlk 11'ler henüz açıklanmadı.</i>"

                        TRACKED_MATCHES[takim] = {"last_goal_count": m['goals']['home'] + m['goals']['away']}
                        tg_post(text)
                    else:
                        tg_post(f"❌ <b>{takim.upper()}</b> için bugün oynanan canlı maç bulunamadı.")
                else:
                    tg_post("❌ Kullanım: <code>/ac galatasaray</code>")

    except: pass
    return "OK", 200

def check_goals():
    headers = {'x-rapidapi-key': FOOTBALL_API_KEY, 'x-rapidapi-host': "v3.football.api-sports.io"}
    for takim in list(TRACKED_MATCHES.keys()):
        try:
            url = f"https://v3.football.api-sports.io/fixtures?live=all&search={takim}"
            res = requests.get(url, headers=headers, timeout=5).json()
            if res.get("response"):
                m = res["response"][0]
                total_goals = m['goals']['home'] + m['goals']['away']
                
                if total_goals > TRACKED_MATCHES[takim]["last_goal_count"]:
                    events = m.get('events', [])
                    goal_ev = [e for e in events if e['type'] == 'Goal'][-1]
                    
                    player = goal_ev['player']['name']
                    assist = goal_ev['assist']['name'] if goal_ev['assist']['name'] else "Yok"
                    minute = goal_ev['time']['elapsed']
                    
                    text = (f"⚽ <b>GOOOOOOOOLLLL!</b>\n"
                            f"───────────────────\n"
                            f"🥅 <b>Skor:</b> {m['goals']['home']} - {m['goals']['away']}\n"
                            f"👤 <b>Gol:</b> {player}\n"
                            f"🎯 <b>Asist:</b> {assist}\n"
                            f"🕒 <b>Dakika:</b> {minute}'\n"
                            f"───────────────────")
                    tg_post(text)
                    TRACKED_MATCHES[takim]["last_goal_count"] = total_goals
        except: pass

@app.route('/get_data')
def get_data():
    r_data = {"result": []}
    try:
        r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live", timeout=8).json()
        if r.get("result"):
            r_data = r
            son = r["result"][0]
            if son["earthquake_id"] != LAST_NOTIFIED_ID[0]:
                if float(son["mag"]) >= 1.5:
                    msg = f"🔔 <b>YENİ DEPREM</b>\n\n📊 <b>Büyüklük:</b> {son['mag']} ({get_risk_info(son['mag'])})\n📍 <b>Yer:</b> {son['title']}\n📏 <b>Derinlik:</b> {son['depth']} km"
                    tg_post(msg)
                LAST_NOTIFIED_ID[0] = son["earthquake_id"]
    except: pass
    
    if TRACKED_MATCHES:
        check_goals()

    return jsonify(r_data)

if __name__ == '__main__': app.run()
