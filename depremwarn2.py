# app.py
from flask import Flask, render_template, abort
import re

app = Flask(__name__)

# Örnek deprem verisi (gerçekte API'den veya veri tabanından çekiyorsun)
depremler = [
    {
        "date": "2024-06-10",
        "title": "Manisa (Ege Bölgesi)",
        "mag": 4.2,
        "depth": 7.4,
        "lat": 38.6,
        "lng": 27.4,
    },
    {
        "date": "2024-06-09",
        "title": "Ankara (İç Anadolu)",
        "mag": 3.6,
        "depth": 5.0,
        "lat": 39.9,
        "lng": 32.8,
    }
]

@app.route("/")
def index():
    return "Ana Sayfa — /onceki ile önceki depremleri görebilirsiniz."

@app.route("/onceki")
def onceki():
    return render_template("onceki.html", depremler=depremler)

@app.route("/detay/")
def detay_bos():
    return "Hatalı bağlantı. Lütfen /onceki sayfasından bir bölge seçin."

@app.route("/detay/<bolge>")
def detay(bolge):
    secilen = next((d for d in depremler if re.search(r'\((.*?)\)', d["title"]) and re.search(r'\((.*?)\)', d["title"]).group(1) == bolge), None)
    if not secilen:
        abort(404)

    risk = "Riskli" if secilen["mag"] >= 4.0 else "Normal"
    return render_template("detay.html", deprem=secilen, risk=risk)

if __name__ == "__main__":
    app.run(debug=True)
