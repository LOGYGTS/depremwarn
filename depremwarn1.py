from flask import Flask, render_template, jsonify
import requests
from datetime import datetime
import re

app = Flask(__name__)

KANDILLI_URL = "http://www.koeri.boun.edu.tr/scripts/lst9.asp"


def get_parantez_ici(title):
    match = re.search(r"\((.*?)\)", title)
    return match.group(1) if match else None


def fetch_kandilli_data():
    """Kandilli web sayfasından deprem listesini çeker ve JSON olarak döndürür."""
    resp = requests.get(KANDILLI_URL)
    resp.encoding = 'latin-1'
    text = resp.text

    lines = text.splitlines()
    pattern = re.compile(
        r"^\s*\d+\s+(\d{4}\.\d{2}\.\d{2})\s+(\d{2}:\d{2}:\d{2})\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+|[-–])\s+([-\d\.]+|[-–])\s+([-\d\.]+|[-–])\s+(.*)$"
    )

    depremler = []
    for line in lines:
        m = pattern.match(line)
        if not m:
            continue

        tarih = m.group(1).strip()
        saat = m.group(2).strip()
        enlem = m.group(3).strip()
        boylam = m.group(4).strip()
        derinlik = m.group(5).strip()
        md = m.group(6).strip()
        ml = m.group(7).strip()
        mw = m.group(8).strip()
        yer = m.group(9).strip()

        deprem = {
            "title": yer,
            "date": f"{tarih} {saat}",
            "mag": ml if ml not in ["-", "–"] else None,
            "depth": derinlik,
            "lat": enlem,
            "lon": boylam,
        }
        depremler.append(deprem)

    return depremler


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/deprem")
def deprem_api():
    try:
        data = fetch_kandilli_data()
        if not data:
            return jsonify({"error": "Deprem verisi alınamadı"})

        current = data[0]  # en son deprem
        bolge = get_parantez_ici(current["title"])

        # Tarih formatı: YYYY.MM.DD HH:MM:SS
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
            "lat": current["lat"],
            "lon": current["lon"],
            "bolge": bolge,
            "fark": fark
        })

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/onceki")
def onceki():
    try:
        data = fetch_kandilli_data()
        return render_template("onceki.html", depremler=data)
    except Exception as e:
        return f"Hata: {e}"


if __name__ == "__main__":
    app.run(debug=True)
