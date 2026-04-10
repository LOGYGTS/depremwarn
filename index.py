from flask import Flask, jsonify, render_template_string
import requests
import re
from bs4 import BeautifulSoup

app = Flask(__name__)

# Buraya senin HTML kodunu "Metin" olarak koyuyoruz (Daha güvenli)
HTML_SABLONU = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>Sismik Risk Paneli</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 0; background: #0f172a; color: white; overflow: hidden; }
        header { background: #1e293b; padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #3b82f6; }
        #live-clock { font-family: monospace; font-size: 1.6rem; color: #60a5fa; }
        .dashboard { display: flex; height: calc(100vh - 82px); }
        #map { flex: 2; height: 100%; border-right: 1px solid #334155; }
        .sidebar { flex: 1; background: #1e293b; overflow-y: auto; padding: 15px; }
        .quake-card { background: #334155; margin-bottom: 12px; padding: 15px; border-radius: 10px; border-left: 6px solid #3b82f6; cursor: pointer; transition: 0.2s; }
        .risk-indicator { display: inline-flex; align-items: center; gap: 6px; font-size: 0.75rem; font-weight: bold; padding: 4px 8px; border-radius: 20px; background: rgba(0,0,0,0.2); }
        .dot { width: 8px; height: 8px; border-radius: 50%; display: inline-block; }
    </style>
</head>
<body>
    <header><h1>📡 SİSMİK RİSK ANALİZ PANELİ</h1><div id="live-clock">00:00:00</div></header>
    <div class="dashboard"><div id="map"></div><div class="sidebar" id="liste">Yükleniyor...</div></div>
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
                data.result.slice(0, 50).forEach((q, i) => {
                    const coords = q.geojson.coordinates;
                    const risk = q.risk_analysis;
                    html += `<div class="quake-card" onclick="map.setView([${coords[1]},${coords[0]}],10); marker.setLatLng([${coords[1]},${coords[0]}]).bindPopup('${q.title}').openPopup();">
                        <div style="display:flex; justify-content:space-between;">
                            <b style="font-size:1.5rem">${q.mag}</b>
                            <div class="risk-indicator" style="color:${risk.color}"><span class="dot" style="background-color:${risk.color}"></span>${risk.status}</div>
                        </div>
                        <div>${q.title}</div>
                        <div style="font-size:0.8rem; color:#94a3b8">Saat: ${q.custom_hour}</div>
                    </div>`;
                });
                document.getElementById('liste').innerHTML = html;
            } catch(e) { console.log(e); }
        }
        updateData(); setInterval(updateData, 30000);
    </script>
</body>
</html>
"""

def sismik_risk_etiketi(mag, derinlik):
    mag = float(mag)
    derinlik = float(derinlik) if derinlik else 10.0
    if mag >= 4.0 or (mag >= 3.5 and derinlik < 10):
        return {"status": "RİSKLİ", "color": "#ff4444"}
    elif mag >= 3.0:
        return {"status": "ORTA", "color": "#ffbb33"}
    else:
        return {"status": "GÜVENLİ", "color": "#00C851"}

@app.route('/')
def index():
    return render_template_string(HTML_SABLONU)

@app.route('/get_data')
def get_data():
    try:
        api_res = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live", timeout=10)
        api_data = api_res.json()
        k_res = requests.get("http://www.koeri.boun.edu.tr/scripts/lst6.asp", timeout=10)
        k_res.encoding = 'utf-8'
        soup = BeautifulSoup(k_res.text, 'html.parser')
        pre_text = soup.find('pre').text
        ham_saatler = re.findall(r'(\d{2}:\d{2}:\d{2})', pre_text)
        if api_data.get("result"):
            for i in range(len(api_data["result"])):
                q = api_data["result"][i]
                q["custom_hour"] = ham_saatler[i] if i < len(ham_saatler) else "00:00:00"
                q["risk_analysis"] = sismik_risk_etiketi(q["mag"], q["depth"])
        return jsonify(api_data)
    except:
        return jsonify({"result": []})