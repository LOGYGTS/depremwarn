from flask import Flask, render_template, jsonify
import requests
from datetime import datetime
import re

app = Flask(__name__)

API_URL = "https://api.orhanaydogdu.com.tr/deprem/kandilli/live"

def get_parantez_ici(title):
    import re
    match = re.search(r"\((.*?)\)", title)
    return match.group(1) if match else None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/deprem")
def deprem_api():
    try:
        data = requests.get(API_URL).json()["result"]
        current = data[0]
        bolge = get_parantez_ici(current["title"])
        current_dt = datetime.strptime(current["date"], "%Y.%m.%d %H:%M:%S")

        fark = "Önceki deprem bulunamadı"
        for d in data[1:]:
            if get_parantez_ici(d["title"]) == bolge:
                dt = datetime.strptime(d["date"], "%Y.%m.%d %H:%M:%S")
                fark = f"{int((current_dt - dt).total_seconds() // 60)} dakika önce"
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

# —————— BURAYA /onceki ROUTE’U EKLİYORUZ ——————
@app.route("/onceki")
def onceki():
    try:
        data = requests.get(API_URL).json()["result"]
        return render_template("onceki.html", depremler=data)
    except Exception as e:
        return f"Hata: {e}"

if __name__ == "__main__":
    app.run(debug=True)
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
