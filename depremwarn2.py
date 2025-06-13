from flask import Flask, render_template, request, abort
import json
import os

app = Flask(__name__)

# Sahte veriler / JSON dosyasindan okuma
def load_data():
    with open("depremler.json", "r", encoding="utf-8") as f:
        return json.load(f)

@app.route("/")
def index():
    depremler = load_data()
    return render_template("index.html", depremler=depremler)

@app.route("/onceki")
def onceki():
    depremler = load_data()
    return render_template("onceki.html", depremler=depremler)

@app.route("/detay/<region>")
def detay(region):
    depremler = load_data()
    secilen = [d for d in depremler if region.lower() in d["title"].lower()]
    if not secilen:
        abort(404)

    detay = secilen[0]
    risk = "Normal"
    if float(detay["mag"]) >= 5.0:
        risk = "Riskli"

    return render_template("detay.html", detay=detay, risk=risk)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
