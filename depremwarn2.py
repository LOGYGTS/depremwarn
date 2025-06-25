from flask import Flask, jsonify, render_template, request
import requests
from datetime import datetime
import os

app = Flask(__name__)

def get_parantez_ici(text):
    start = text.find("(")
    end = text.find(")")
    if start != -1 and end != -1:
        return text[start+1:end].strip()
    return ""

@app.route("/")
def index():
    # templates klasöründe index.html dosyan olmalı
    return render_template("index.html")

@app.route("/onceki")
def onceki():
    return "<h2>Önceki depremler sayfası buraya gelecek</h2>"

@app.route("/haritalar")
def haritalar():
    return "<h2>Haritalar sayfası buraya gelecek</h2>"

@app.route("/api/deprem")
def deprem_api():
    source = request.args.get("source", "kandilli")

    if source == "kandilli":
        api_url = "https://api.orhanaydogdu.com.tr/deprem/kandilli/live"
    elif source == "emsc":
        api_url = "https://api.orhanaydogdu.com.tr/deprem/emsc/live"
    else:
        return jsonify({"error": "Geçersiz kaynak"}), 400

    try:
        response = requests.get(api_url, timeout=5)
        response.raise_for_status()  # HTTP hata kontrolü
        data = response.json().get("result", [])
        if not data:
            return jsonify({"error": "Veri bulunamadı"}), 404

        current = data[0]
        bolge = get_parantez_ici(current["title"])
        current_dt = datetime.strptime(current["date"], "%Y.%m.%d %H:%M:%S")

        fark = "Önceki deprem bulunamadı"
        for d in data[1:]:
            if get_parantez_ici(d["title"]) == bolge:
                dt = datetime.strptime(d["date"], "%Y.%m.%d %H:%M:%S")
                dakika_fark = int((current_dt - dt).total_seconds() // 60)
                fark = f"{dakika_fark} dk"
                break

        return jsonify({
            "title": current["title"],
            "mag": current["mag"],
            "depth": current["depth"],
            "date": current["date"],
            "lat": current["geojson"]["coordinates"][1],
            "lon": current["geojson"]["coordinates"][0],
            "bolge": bolge,
            "fark": fark
        })

    except requests.exceptions.RequestException as e:
        return jsonify({"error": "API bağlantı hatası: " + str(e)}), 500
    except Exception as e:
        return jsonify({"error": "İşlem hatası: " + str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # debug=False deploy için önemli
    app.run(debug=False, host="0.0.0.0", port=port)
