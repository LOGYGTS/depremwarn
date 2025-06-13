from flask import Flask, render_template, jsonify
import requests
from datetime import datetime
import re

app = Flask(__name__)

API_URL = "https://api.orhanaydogdu.com.tr/deprem/kandilli/live"

def get_parantez_ici(title):
    match = re.search(r"\((.*?)\)", title)
    return match.group(1) if match else "Bilinmeyen"

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

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/onceki")
def onceki():
    try:
        data = requests.get(API_URL).json()["result"]
        for d in data:
            d["bolge"] = get_parantez_ici(d["title"])
        return render_template("onceki.html", depremler=data)
    except Exception as e:
        return f"Hata: {e}"

@app.route("/detay/<bolge>")
def detay(bolge):
    try:
        data = requests.get(API_URL).json()["result"]
        secili = None
        onceki = None

        for i, d in enumerate(data):
            if get_parantez_ici(d["title"]) == bolge:
                secili = d
                for diger in data[i+1:]:
                    if get_parantez_ici(diger["title"]) == bolge:
                        secili_dt = datetime.strptime(d["date"], "%Y.%m.%d %H:%M:%S")
                        diger_dt = datetime.strptime(diger["date"], "%Y.%m.%d %H:%M:%S")
                        fark = int((secili_dt - diger_dt).total_seconds() // 60)
                        onceki = fark
                        break
                break

        if not secili:
            return f"{bolge} bölgesi için deprem verisi bulunamadı."

        return render_template("detay.html", deprem=secili, bolge=bolge, fark=onceki)
    except Exception as e:
        return f"Hata: {e}"

if __name__ == "__main__":
    app.run(debug=True)
