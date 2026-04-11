from flask import Flask, jsonify, render_template_string, redirect, url_for
import requests
import re
import random
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = "8661340862:AAF2uR2fwN0aSHES65xB7uswA1ceuQcZhw8"
CHAT_ID = "-1005272137007" 
LAST_NOTIFIED_ID = [None]

def sismik_risk_etiketi(mag):
    mag = float(mag)
    if mag >= 4.0: return "🔴 RİSKLİ"
    elif mag >= 3.0: return "🟡 ORTA"
    return "🟢 GÜVENLİ"

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"}
    try:
        r = requests.post(url, data=payload, timeout=10)
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}

@app.route('/')
def index():
    # Mevcut harita HTML şablonun burada kalmaya devam edecek
    return "Harita Paneli Aktif (Kodun üst kısmındaki HTML_SABLONU buraya gelecek)"

@app.route('/test')
def test_son_deprem():
    try:
        # En son deprem verisini çekiyoruz
        api_res = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live", timeout=10)
        api_data = api_res.json()
        
        # Kandilli'den saatleri çekiyoruz
        k_res = requests.get("http://www.koeri.boun.edu.tr/scripts/lst6.asp", timeout=10)
        k_res.encoding = 'utf-8'
        soup = BeautifulSoup(k_res.text, 'html.parser')
        ham_saatler = re.findall(r'(\d{2}:\d{2}:\d{2})', soup.find('pre').text)

        if api_data.get("result"):
            son = api_data["result"][0]
            mag = son["mag"]
            yer = son["title"]
            derinlik = son["depth"]
            saat = ham_saatler[0] if ham_saatler else son["date_time"].split(" ")[1]
            risk = sismik_risk_etiketi(mag)

            mesaj = (
                f"🚀 <b>MANUEL TEST (SON DEPREM)</b>\n\n"
                f"📍 Yer: {yer}\n"
                f"📊 Büyüklük: <b>{mag}</b>\n"
                f"⏰ Saat: {saat}\n"
                f"📉 Derinlik: {derinlik} km\n"
                f"🚦 Risk Durumu: {risk}\n\n"
                f"✅ Bot bağlantısı ve veri çekme başarılı!"
            )
            
            res = telegram_gonder(mesaj)
            if res.get("ok"):
                return "✅ Son deprem bilgisi gruba başarıyla gönderildi!"
            else:
                return f"❌ Mesaj Gönderilemedi! Hata: {res.get('description')}"
        
        return "❌ Deprem verisi alınamadı."
    except Exception as e:
        return f"❌ Sistem Hatası: {str(e)}"

# Get_data rotası ve diğer fonksiyonların değişmeden kalmalı...
