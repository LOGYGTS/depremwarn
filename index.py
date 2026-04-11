from flask import Flask, jsonify, render_template_string, redirect, url_for
import requests
import re
import random
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = "8661340862:AAF2uR2fwN0aSHES65xB7uswA1ceuQcZhw8"
CHAT_ID = "-5272137007" 
LAST_NOTIFIED_ID = [None]

# Harita Tasarımı
HTML_SABLONU = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sismik Risk Paneli</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #0f172a; color: white; overflow: hidden; }
        header { background: #1e293b; padding: 15px; display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #3b82f6; }
        #live-clock { font-family: monospace; font-size: 1.4rem; color: #60a5fa; }
        .dashboard { display: flex; height: calc(100vh - 70px); flex-direction: column; }
        #map { height: 40%; width: 100%; border-bottom: 1px solid #334155; }
        .sidebar { flex: 1; background: #1e293b; overflow-y: auto; padding: 10px; }
        .quake-card { background: #334155; margin-bottom: 10px; padding: 15px; border-radius: 10px; border-left: 6px solid #3b82f6; cursor: pointer; }
        @media (min-width: 768px) { .dashboard { flex-direction: row; } #map { height: 100%; flex: 2; border-bottom: none; border-right: 1px solid #334155; } }
    </style>
</head>
<body>
    <header><h3>📡 SİSMİK RİSK ANALİZİ</h3><div id="live-clock">00:00:00</div></header>
    <div class="dashboard"><div id="map"></div><div class="sidebar" id="liste">Veriler yükleniyor...</div></div>
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        let map = L.map('map').setView([39.0, 35.0], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        let marker = L.marker([39.0, 35.0]).addTo(map);
        setInterval(() => { document.getElementById('live-clock').innerText = new Date().toLocaleTimeString('tr-TR'); }, 1000);
        async function updateData() {
            try {
                const res = await fetch('/get_data');
                const data = await res.json();
                let html = "";
                data.result.slice(0, 30).forEach((q) => {
                    const coords = q.geojson.coordinates;
                    html += `<div class="quake-card" onclick="map.setView([${coords[1]},${coords[0]}],10); marker.setLatLng([${coords[1]},${coords[0]}]).bindPopup('${q.title}').openPopup();">
                        <b>${q.mag}</b> - ${q.title}<br><small>Saat: ${q.custom_hour} | Derinlik: ${q.depth}km</small>
                    </div>`;
                });
                document.getElementById('liste').innerHTML = html;
            } catch(e) { console.log(e); }
        }
        updateData(); setInterval(updateData, 25000);
    </script>
</body>
</html>
"""

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload, timeout=10)
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.route('/')
def index():
    return render_template_string(HTML_SABLONU)

@app.route('/test')
def test_mesaji():
    mag = round(random.uniform(3.0, 5.0), 1)
    mesaj = f"🚀 <b>BAĞLANTI TESTİ</b>\\n\\n📊 Büyüklük: {mag}\\n✅ Bot ve Panel şu an eşleşti!"
    sonuc = telegram_gonder(mesaj)
    if sonuc.get("ok"):
        # Mesaj giderse direkt ana sayfaya yönlendir
        return redirect(url_for('index'))
    else:
        return f"❌ Mesaj Gönderilemedi! Hata: {sonuc.get('description')} | CHAT_ID: {CHAT_ID}"

@app.route('/get_data')
def get_data():
    try:
        api_res = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live", timeout=10)
        api_data = api_res.json()
        k_res = requests.get("http://www.koeri.boun.edu.tr/scripts/lst6.asp", timeout=10)
        k_res.encoding = 'utf-8'
        soup = BeautifulSoup(k_res.text, 'html.parser')
        ham_saatler = re.findall(r'(\d{2}:\d{2}:\d{2})', soup.find('pre').text)

        if api_data.get("result"):
            ilk = api_data["result"][0]
            if ilk["earthquake_id"] != LAST_NOTIFIED_ID[0]:
                mag = float(ilk["mag"])
                if mag >= 1.5:
                    saat = ham_saatler[0] if ham_saatler else "--:--"
                    m = f"🔔 <b>YENİ DEPREM</b>\\n\\n📍 Yer: {ilk['title']}\\n📊 Büyüklük: {mag}\\n⏰ Saat: {saat}"
                    telegram_gonder(m)
                LAST_NOTIFIED_ID[0] = ilk["earthquake_id"]

            for i in range(len(api_data["result"])):
                q = api_data["result"][i]
                q["custom_hour"] = ham_saatler[i] if i < len(ham_saatler) else "00:00"
        return jsonify(api_data)
    except Exception as e:
        return jsonify({"result": [], "error": str(e)})

# Vercel için gerekli olan kısım
if __name__ == '__main__':
    app.run(debug=True)
