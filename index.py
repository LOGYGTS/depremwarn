from flask import Flask, jsonify, render_template_string, request
import requests

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = "8661340862:AAF2F7wpAvuFsH1xAtaYWBi-A0mG6ZiYPsY"
CHAT_ID = "-1003273342330"
FOOTBALL_API_KEY = "BURAYA_RAPIDAPI_KEY_GELECEK" # RapidAPI'den alınan key
LAST_NOTIFIED_ID = [None]

# TAKİP EDİLEN MAÇLAR (Hafızada tutulur)
TRACKED_MATCHES = {} 

def tg_post(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=5)

def get_risk_info(mag):
    m = float(mag)
    if m >= 4.0: return "🔴 RİSKLİ"
    if m >= 3.0: return "🟡 ORTA"
    return "🟢 GÜVENLİ"

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        upd = request.get_json()
        if "message" in upd and "text" in upd["message"]:
            msg = upd["message"]["text"].lower()
            
            # --- /ac Komutu (Örn: /ac galatasaray) ---
            if msg.startswith("/ac"):
                takim = msg.replace("/ac", "").strip()
                if takim:
                    # Burada API'den canlı maç araması yapılır
                    TRACKED_MATCHES[takim] = {"last_goal_count": 0}
                    tg_post(f"✅ <b>{takim.upper()}</b> maçı takibe alındı. Gol olduğunda detaylı bilgi vereceğim.")
                else:
                    tg_post("❌ Lütfen bir takım adı yazın. Örn: <code>/ac fenerbahçe</code>")

            # --- /kapat Komutu ---
            elif msg.startswith("/kapat"):
                takim = msg.replace("/kapat", "").strip()
                if takim in TRACKED_MATCHES:
                    del TRACKED_MATCHES[takim]
                    tg_post(f"📴 <b>{takim.upper()}</b> maçı takibi durduruldu.")

            # --- Deprem Komutları (Aynen Korundu) ---
            elif "/deprem" in msg:
                r = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live").json()
                son = r["result"][0]
                text = f"📢 <b>SON DEPREM</b>\n\n📊 <b>Büyüklük:</b> {son['mag']} ({get_risk_info(son['mag'])})\n📍 <b>Yer:</b> {son['title']}\n⏰ <b>Saat:</b> {son['date_time']}"
                tg_post(text)
    except: pass
    return "OK", 200

# Bu fonksiyon arka planda (veya get_data her çalıştığında) maçları kontrol eder
def check_live_goals():
    headers = {'x-rapidapi-key': FOOTBALL_API_KEY, 'x-rapidapi-host': "v3.football.api-sports.io"}
    
    for takim in list(TRACKED_MATCHES.keys()):
        # Canlı skorları çek (API Endpoint örneğidir)
        url = f"https://v3.football.api-sports.io/fixtures?live=all&search={takim}"
        res = requests.get(url, headers=headers).json()
        
        if res.get("response"):
            match = res["response"][0]
            goals = match['events'] # Maç olayları
            current_goals = match['goals']['home'] + match['goals']['away']
            
            if current_goals > TRACKED_MATCHES[takim]["last_goal_count"]:
                # Son golü bul
                last_event = [e for e in goals if e['type'] == 'Goal'][-1]
                player = last_event['player']['name']
                assist = last_event['assist']['name'] if last_event['assist']['name'] else "Yok"
                minute = last_event['time']['elapsed']
                score = f"{match['goals']['home']} - {match['goals']['away']}"
                
                text = (f"⚽ <b>GOOOOOOOOLLLL!</b>\n"
                        f"───────────────────\n"
                        f"🏟️ <b>Maç:</b> {match['teams']['home']['name']} vs {match['teams']['away']['name']}\n"
                        f"🥅 <b>Skor:</b> {score}\n"
                        f"👤 <b>Gol:</b> {player}\n"
                        f"🎯 <b>Asist:</b> {assist}\n"
                        f"🕒 <b>Dakika:</b> {minute}'\n"
                        f"───────────────────")
                tg_post(text)
                TRACKED_MATCHES[takim]["last_goal_count"] = current_goals

@app.route('/get_data')
def get_data():
    # Deprem kontrolü (Mevcut kodun)
    # ... (Burada deprem kodların çalışmaya devam eder) ...
    
    # Maç kontrolü
    if TRACKED_MATCHES:
        check_live_goals()
        
    return jsonify({"status": "ok"})
