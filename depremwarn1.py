from flask import Flask, render_template, jsonify
import requests
import re
from datetime import datetime

app = Flask(__name__)

KANDILLI_URL = "http://www.koeri.boun.edu.tr/scripts/lst9.asp"

def get_parantez_ici(title):
    match = re.search(r"\((.*?)\)", title)
    return match.group(1) if match else None


def fetch_kandilli_data():
    """Kandilli web sayfasından en son depremleri çeker ve JSON döner."""
    try:
        resp = requests.get(KANDILLI_URL, timeout=10)
        resp.encoding = resp.apparent_encoding  # otomatik tanıma
        text = resp.text

        # <pre> etiketi varsa sadece içeriğini al
        pre_match = re.search(r"<pre>(.*?)</pre>", text, re.DOTALL | re.IGNORECASE)
        if pre_match:
            text = pre_match.group(1)

        lines = text.splitlines()

        # Kandilli satır formatı genelde sabit genişlikte
        pattern = re.compile(
            r"^\s*\d+\s+(\d{4}\.\d{2}\.\d{2})\s+(\d{2}:\d{2}:\d{2})\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+)\s+([-\d\.]+|[-–])\s+([-\d\.]+|[-–])\s+([-\d\.]+|[-–])\s+(.*)$"
        )

        earthquakes = []
        for line in lines:
            m = pattern.match(line)
            if not m:
                continue

            tarih, saat, lat, lon, derinlik, md, ml, mw, yer = [g.strip() for g in m.groups()]

            earthquakes.append({
                "title": yer,
                "date": f"{tarih} {saat}",
                "mag": ml if ml not in ["-", "–"] else None,
                "depth": derinlik,
                "lat": lat,
                "lon": lon
            })

        if not earthquakes:
            raise ValueError("Veri parse edilemedi (regex eşleşmedi).")

        return earthquakes

    except Exception as e:
        print("Kandilli veri çekme hatası:", e)
        return []


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/deprem")
def deprem_api():
    try:
        data = fetch_kandilli_data()
        if not data:
            return jsonify({"error": "Kandilli verisi alınamadı"})

        current = data[0]
        bolge = get_parantez_ici(current["title"])

        try:
            current_dt = datetime.strptime(current["date"], "%Y.%m.%d %H:%M:%S")
        except ValueError:
            # tarih formatı değişmişse burada hata almamak için düzelt
            current_dt = datetime.now()

        fark = "Önceki deprem bulunamadı"
        for d in data[1:]:
            if get_parantez_ici(d["title"]) == bolge:
                try:
                    dt = datetime.strptime(d["date"], "%Y.%m.%d %H:%M:%S")
                    dakika_fark = int((current_dt - dt).total_seconds() // 60)
                    fark = f"{dakika_fark} dk"
                except:
                    fark = "Zaman farkı hesaplanamadı"
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
        if not data:
            return "Kandilli verisi alınamadı."
        return render_template("onceki.html", depremler=data)
    except Exception as e:
        return f"Hata: {e}"


if __name__ == "__main__":
    app.run(debug=True)
