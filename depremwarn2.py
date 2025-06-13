from flask import Flask, render_template, jsonify
import requests
from datetime import datetime
import re

app = Flask(__name__)

API_URL = "https://api.orhanaydogdu.com.tr/deprem/kandilli/live"

def get_parantez_ici(title):
    match = re.search(r"\((.*?)\)", title)
    return match.group(1) if match else None

@app.template_filter("regex_search")
def regex_search(s, pattern, group=1):
    match = re.search(pattern, s)
    return match.group(group) if match else s

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
        return render_template("onceki.html", depremler=data)
    except Exception as e:
        return f"Hata: {e}"

@app.route("/detay/<path:bolge>")
def detay(bolge):
    try:
        data = requests.get(API_URL).json()["result"]
        bolgedeki = [d for d in data if get_parantez_ici(d["title"]) == bolge]

        if not bolgedeki:
            return f"{bolge} için detay bulunamadı."

        son = bolgedeki[0]
        onceki = bolgedeki[1] if len(bolgedeki) > 1 else None

        fark = "Önceki deprem bulunamadı"
        if onceki:
            dt1 = datetime.strptime(son["date"], "%Y.%m.%d %H:%M:%S")
            dt2 = datetime.strptime(onceki["date"], "%Y.%m.%d %H:%M:%S")
            dakika_fark = int((dt1 - dt2).total_seconds() // 60)
            fark = f"{dakika_fark} dk"

        return render_template("detay.html", deprem=son, fark=fark)

    except Exception as e:
        return f"Hata: {e}"

if __name__ == "__main__":
    app.run(debug=True)
