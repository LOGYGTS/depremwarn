import requests
import re
from flask import Flask, jsonify, render_template_string
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = "8661340862:AAF6rHBe2ZfSr1pYGqc52V4-Gup8yIwu60I"
CHAT_ID = "-1003273342330"
# Bellekte son depremi tutmak için (Vercel sıfırlayabilir, Cron-Job ile desteklenmeli)
LAST_NOTIFIED_ID = [None] 

# Web Paneli İçin HTML Şablonu
HTML_SABLONU = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Sismik Risk Paneli</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #0f172a; color: white; }
        header { background: #1e293b; padding: 15px; text-align: center; border-bottom: 3px solid #3b82f6; }
        .dashboard { display: flex; height: calc(100vh - 70px); }
        #map { flex: 2; height: 100%; }
        .sidebar { flex: 1; background: #1e293b; overflow-y: auto; padding: 15px; }
        .quake-card { background: #334155; margin-bottom: 10px; padding: 15px; border-radius: 8px; border-left: 5px solid #3b82f6; cursor: pointer; }
        .risk-badge { float: right; padding: 3px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; }
    </style>
</head>
<body>
    <header><h1>📡 SİSMİK TAKİP VE ANALİZ SİSTEMİ</h1></header>
    <div class="dashboard">
        <div id="map"></div>
        <div class="sidebar" id="liste">Veriler yükleniyor...</div>
    </div>
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
                data.result.slice(0, 30).forEach(q => {
                    const coords = q.geojson.coordinates;
                    html += `<div class="quake-card" onclick="map.setView([${coords[1]},${coords[0]}],9); marker.setLatLng([${coords[1]},${coords[0]}]).bindPopup('${q.title}').openPopup();">
                        <span class="risk-badge" style="color:${q.risk_analysis.color}">${q.risk_analysis.status}</span>
                        <b>${q.mag}</b> - ${q.title}<br>
                        <small style="color:#94a3b8">${q.date}</small>
                    </div>`;
                });
                document.getElementById('liste').innerHTML = html;
            } catch(e) { console.error(e); }
        }
        updateData();
        setInterval(updateData, 60000); // 1 dakikada bir yenile
    </script>
</body>
</html>
"""

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=5)
    except:
        pass

def risk_analizi(mag):
    mag = float(mag)
    if mag >= 4.5: return {"status": "🚨 RİSKLİ", "color": "#ff4444"}
    if mag >= 3.5: return {"status": "⚠️ ORTA", "color": "#ffbb33"}
    return {"status": "✅ GÜVENLİ", "color": "#00C851"}

@app.route('/')
def index():
    return render_template_string(HTML_SABLONU)

@app.route('/get_data')
def get_data():
    try:
        # API'den verileri al
        api_res = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live", timeout=10)
        api_data = api_res.json()

        if api_data.get("result"):
            # BOT KONTROLÜ: En son deprem 2.5 üstü mü ve yeni mi?
            son_deprem = api_data["result"][0]
            mag = float(son_deprem["mag"])
            d_id = son_deprem["earthquake_id"]

            if mag >= 2.5 and d_id != LAST_NOTIFIED_ID[0]:
                risk = risk_analizi(mag)
                maps_link = f"https://www.google.com/maps?q={son_deprem['geojson']['coordinates'][1]},{son_deprem['geojson']['coordinates'][0]}"
                
                mesaj = (
                    f"🔔 <b>YENİ DEPREM BİLDİRİMİ</b>\n\n"
                    f"📍 <b>Yer:</b> {son_deprem['title']}\n"
                    f"📊 <b>Büyüklük:</b> {mag}\n"
                    f"📉 <b>Derinlik:</b> {son_deprem['depth']} km\n"
                    f"⏰ <b>Saat:</b> {son_deprem['date']}\n"
                    f"🚦 <b>Analiz:</b> {risk['status']}\n\n"
                    f"📍 <a href='{maps_link}'>Haritada Görüntüle</a>"
                )
                telegram_gonder(mesaj)
                LAST_NOTIFIED_ID[0] = d_id

            # WEB PANELİ İÇİN VERİLERİ ETİKETLE
            for q in api_data["result"]:
                q["risk_analysis"] = risk_analizi(q["mag"])

        return jsonify(api_data)
    except Exception as e:
        return jsonify({"result": [], "error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
