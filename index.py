from flask import Flask, jsonify, render_template_string, request
import requests

app = Flask(__name__)

# --- GÜNCEL BİLGİLERİN ---
# Token ve Chat ID'ni buraya tam olarak yapıştır
TELEGRAM_TOKEN = "8661340862:AAF2F7wpAvuFsH1xAtaYWBi-A0mG6ZiYPsY"
CHAT_ID = "-1003826426476"
LAST_NOTIFIED_ID = [None]

# ANA SAYFA TASARIMI (Görseldekiyle Birebir)
HTML_SABLONU = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sismik Risk Analiz Paneli</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        /* Birebir Tasarım İçin CSS */
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background: #0b1120; color: white; display: flex; flex-direction: column; height: 100vh; overflow: hidden; }
        header { background: #1e293b; padding: 12px 20px; border-bottom: 2px solid #334155; display: flex; justify-content: space-between; align-items: center; z-index: 1000; flex-shrink: 0; }
        .live-clock { color: #60a5fa; font-family: monospace; font-size: 1.1rem; }
        
        .main-container { display: flex; flex: 1; overflow: hidden; }
        
        /* Sol Taraf: Harita */
        #map { flex: 2; height: 100%; border-right: 1px solid #334155; z-index: 1; }
        
        /* Sağ Taraf: Koyu Tema Dikey Liste */
        .sidebar { flex: 0.8; background: #111827; overflow-y: auto; padding: 10px; display: flex; flex-direction: column; gap: 8px; flex-shrink: 0; }
        
        /* Liste Kartları */
        .quake-card { background: #1f2937; padding: 12px 15px; border-radius: 8px; border-left: 5px solid #10b981; cursor: pointer; transition: 0.2s; position: relative; }
        .quake-card:hover { background: #334155; transform: translateX(3px); }
        
        /* Risk Bilgileri */
        .status-badge { position: absolute; top: 10px; right: 10px; font-size: 0.6rem; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
        
        /* Yazı Stilleri */
        .mag { font-size: 1.4rem; font-weight: bold; margin-bottom: 2px; }
        .loc { font-size: 0.85rem; font-weight: 600; text-transform: uppercase; color: #e2e8f0; margin-bottom: 3px; }
        .time { font-size: 0.75rem; color: #94a3b8; }

        /* Mobil Uyumluluk */
        @media (max-width: 768px) {
            .main-container { flex-direction: column; }
            #map { flex: none; height: 40%; border-right: none; border-bottom: 1px solid #334155; }
            .sidebar { flex: 1; }
        }
    </style>
</head>
<body>
    <header>
        <div>📡 <b>SİSMİK RİSK ANALİZ PANELİ</b></div>
        <div id="clock" class="live-clock">00:00:00</div>
    </header>
    
    <div class="main-container">
        <div id="map"></div>
        <div class="sidebar" id="liste">Yükleniyor...</div>
    </div>

    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        // Canlı Saat
        setInterval(() => { document.getElementById('clock').innerText = new Date().toLocaleTimeString('tr-TR'); }, 1000);

        // Harita Kurulumu (Görseldeki zoom seviyesine yakın)
        let map = L.map('map', {zoomControl: false}).setView([39.0, 35.0], 6);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
        L.control.zoom({position: 'topleft'}).addTo(map);
        let marker = L.marker([39.0, 35.0]).addTo(map);

        async function updateData() {
            try {
                const res = await fetch('/get_data');
                const data = await res.json();
                let html = "";
                data.result.slice(0, 35).forEach((q) => {
                    const coords = q.geojson.coordinates;
                    const mag = parseFloat(q.mag);
                    
                    // --- RİSK ALGORİTMASI ---
                    let riskColor = "#10b981"; // Güvenli (Yeşil)
                    let riskLabel = "🟢 GÜVENLİ";
                    if(mag >= 4.0) { 
                        riskColor = "#ef4444"; // Riskli (Kırmızı)
                        riskLabel = "🔴 RİSKLİ"; 
                    }
                    else if(mag >= 3.0) { 
                        riskColor = "#f59e0b"; // Orta (Sarı)
                        riskLabel = "🟡 ORTA"; 
                    }

                    // Birebir Kart Tasarımı
                    html += `
                    <div class="quake-card" style="border-left-color: ${riskColor}" onclick="focusMap(${coords[1]}, ${coords[0]}, '${q.title}')">
                        <div class="status-badge" style="color:${riskColor}; border: 1px solid ${riskColor}">${riskLabel}</div>
                        <div class="mag" style="color:${riskColor}">${q.mag}</div>
                        <div class="loc">${q.title}</div>
                        <div class="time">Saat: ${q.date_time.split(' ')[1]}</div>
                    </div>`;
                });
                document.getElementById('liste').innerHTML = html;
            } catch(e) { console.error("Veri çekilemedi:", e); }
        }

        function focusMap(lat, lng, title) {
            map.setView([lat, lng], 10);
            marker.setLatLng([lat, lng]).bindPopup(title).openPopup();
            if(window.innerWidth <= 768) document.getElementById('liste').scrollIntoView();
        }

        updateData(); setInterval(updateData, 30000);
    </script>
</body>
</html>
"""

def telegram_gonder(mesaj):
    # \n karakterlerini gerçek satır sonuna çeviriyoruz (Gruptaki hata için)
    clean_text = mesaj.replace("\\n", "\n")
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": clean_text, "parse_mode": "HTML"}, timeout=5)

@app.route('/')
def index(): return render_template_string(HTML_SABLONU)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        if "message" in update and "text" in update["message"]:
            text = update["message"]["text"].lower()
            if "/test" in text:
                telegram_gonder("✅ <b>SİSTEM AKTİF!</b>\nAna site tasarımı ve Telegram bağlantısı sorunsuz çalışıyor.")
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
                    telegram_gonder(msg)
                LAST_NOTIFIED_ID[0] = son["earthquake_id"]
        return jsonify(r)
    except: return jsonify({"result": []})

if __name__ == '__main__': app.run()
