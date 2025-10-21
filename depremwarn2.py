from flask import Flask, render_template, jsonify
import requests
from datetime import datetime
import os
import re
from dateutil import parser  # Tarih formatını esnek parse etmek için

app = Flask(__name__)

API_URL = "https://api.orhanaydogdu.com.tr/deprem/kandilli/live"

def get_parantez_ici(title):
    match = re.search(r"\((.*?)\)", title)
    return match.group(1) if match else None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/deprem")
def deprem_api():
    try:
        response = requests.get(API_URL, timeout=5)
        data = response.json().get("result", [])
        if not data:
            return jsonify({"error": "API boş veri döndürdü"})

        current = data[0]
        bolge = get_parantez_ici(current["title"])
        current_dt = parser.parse(current["date"])  # dateutil ile esnek parse

        fark = "Önceki deprem bulunamadı"
        for d in data[1:]:
            if get_parantez_ici(d["title"]) == bolge:
                dt = parser.parse(d["date"])
                dakika = int((current_dt - dt).total_seconds() // 60)
                fark = f"{dakika} dakika önce"
                break

        return jsonify({
            "title": current["title"],
            "mag": current["mag"],
            "depth": current["depth"],
            "date": current["date"],
            "bolge": bolge,
            "fark": fark
        })

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/onceki")
def onceki():
    try:
        data = requests.get(API_URL, timeout=5).json().get("result", [])
        return render_template("onceki.html", depremler=data)
    except Exception as e:
        return f"Hata: {e}"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
