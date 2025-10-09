from flask import Flask, render_template, jsonify
import requests
from datetime import datetime
import re

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
        resp = requests.get(API_URL, timeout=10)
        data = resp.json()
        # API docs’a göre “live” endpoint doğrudan bir nesne dönebilir, ya da “result” listesi olabilir
        # Örneğin: { "earthquake_id": ..., "title": ..., "date": ..., ... }
        # veya: { "result": [ {...}, {...}, ... ] }
        # Öyleyse önce yapıyı kontrol et:

        # Eğer "result" anahtarı varsa:
        if isinstance(data, dict) and "result" in data:
            results = data["result"]
            if not results:
                return jsonify({"error": "Sonuç listesi boş"})
            current = results[0]
        else:
            # Doğrudan tek nesne gelmiş olabilir
            current = data

        # Gerekli alanların mevcut olup olmadığına bak:
        title = current.get("title") or current.get("lokasyon") or ""
        date_str = current.get("date") or current.get("date_time") or current.get("datetime")
        mag = current.get("mag")
        depth = current.get("depth")
        geojson = current.get("geojson", {})
        coords = geojson.get("coordinates", [None, None])
        # coords: [lon, lat]
        lon = coords[0]
        lat = coords[1]

        # Parse tarihi kontrol et
        current_dt = None
        fark = "Önceki deprem bulunamadı"
        if date_str:
            # API docs örneğinde format "YYYY.MM.DD HH:MM:SS"
            try:
                current_dt = datetime.strptime(date_str, "%Y.%m.%d %H:%M:%S")
            except Exception:
                # Farklı formatta gelmiş olabilir, sadece atla
                pass

        # Eğer “result” listesi geldiyse ve diğer eleman varsa fark hesapla
        if isinstance(data, dict) and "result" in data and len(data["result"]) > 1 and current_dt:
            for d in data["result"][1:]:
                # Aynı bölge kontrolü:
                title2 = d.get("title") or d.get("lokasyon") or ""
                if get_parantez_ici(title2) == get_parantez_ici(title):
                    date2 = d.get("date") or d.get("date_time") or d.get("datetime")
                    if date2:
                        try:
                            dt2 = datetime.strptime(date2, "%Y.%m.%d %H:%M:%S")
                            dakika_fark = int((current_dt - dt2).total_seconds() // 60)
                            fark = f"{dakika_fark} dk"
                        except Exception:
                            pass
                    break

        return jsonify({
            "title": title,
            "mag": mag,
            "depth": depth,
            "date": date_str,
            "lat": lat,
            "lon": lon,
            "bolge": get_parantez_ici(title),
            "fark": fark
        })

    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/onceki")
def onceki():
    try:
        resp = requests.get(API_URL, timeout=10)
        data = resp.json()

        if isinstance(data, dict) and "result" in data:
            results = data["result"]
        else:
            results = [data]

        return render_template("onceki.html", depremler=results)
    except Exception as e:
        return f"Hata: {e}"


if __name__ == "__main__":
    app.run(debug=True)
