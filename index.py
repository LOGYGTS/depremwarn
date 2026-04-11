import requests
import re
import random # Rastgele değerler için eklendi
from flask import Flask, jsonify, render_template_string
from bs4 import BeautifulSoup

app = Flask(__name__)

# --- AYARLAR ---
TELEGRAM_TOKEN = "8661340862:AAF6rHBe2ZfSr1pYGqc52V4-Gup8yIwu60I"
CHAT_ID = "-1003076665434" # Buradaki ~ işareti - yapıldı (Kritik!)
LAST_NOTIFIED_ID = [None] 

# ... (HTML_SABLONU aynı kalıyor, buraya yapıştırabilirsin) ...

def telegram_gonder(mesaj):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mesaj, "parse_mode": "HTML"}
    try:
        res = requests.post(url, data=payload, timeout=5)
        return res.json() # Hata ayıklama için cevabı dön
    except:
        return None

def sismik_risk_etiketi(mag, derinlik):
    mag = float(mag)
    derinlik = float(derinlik) if derinlik else 10.0
    if mag >= 4.0 or (mag >= 3.5 and derinlik < 10):
        return {"status": "RİSKLİ", "color": "#ff4444"}
    elif mag >= 3.0:
        return {"status": "ORTA", "color": "#ffbb33"}
    else:
        return {"status": "GÜVENLİ", "color": "#00C851"}

# --- YENİ TEST FONKSİYONU ---
@app.route('/test')
def test_mesaji():
    test_yerler = ["Marmara Denizi", "Ege Denizi", "Ankara", "İzmir", "İstanbul", "Antalya"]
    test_mag = round(random.uniform(2.5, 5.5), 1)
    test_yer = random.choice(test_yerler)
    test_saat = "12:34:56 (TEST)"
    risk = sismik_risk_etiketi(test_mag, 7.0)
    
    mesaj = (
        f"🚀 <b>SİSTEM TEST BİLDİRİMİ</b>\n\n"
        f"📍 <b>Yer:</b> {test_yer}\n"
        f"📊 <b>Büyüklük:</b> <b>{test_mag}</b>\n"
        f"📉 <b>Derinlik:</b> 7.0 km\n"
        f"⏰ <b>Saat:</b> {test_saat}\n"
        f"🚦 <b>Analiz:</b> {risk['status']}\n\n"
        f"✅ Bot şu an başarıyla çalışıyor ve gruba erişebiliyor."
    )
    sonuc = telegram_gonder(mesaj)
    if sonuc and sonuc.get("ok"):
        return "Test mesajı başarıyla Telegram grubuna gönderildi! Grubu kontrol et."
    else:
        return f"Hata! Mesaj gönderilemedi. Botun grupta admin olduğundan ve ID'nin doğru olduğundan emin ol. Hata kodu: {sonuc}"

@app.route('/')
def index():
    return render_template_string(HTML_SABLONU)

@app.route('/get_data')
def get_data():
    try:
        api_res = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live", timeout=10)
        api_data = api_res.json()
        k_res = requests.get("http://www.koeri.boun.edu.tr/scripts/lst6.asp", timeout=10)
        k_res.encoding = 'utf-8'
        soup = BeautifulSoup(k_res.text, 'html.parser')
        pre_text = soup.find('pre').text
        ham_saatler = re.findall(r'(\d{2}:\d{2}:\d{2})', pre_text)

        if api_data.get("result"):
            ilk_deprem = api_data["result"][0]
            mag = float(ilk_deprem["mag"])
            d_id = ilk_deprem["earthquake_id"]
            
            if mag >= 1.5 and d_id != LAST_NOTIFIED_ID[0]:
                risk = sismik_risk_etiketi(mag, ilk_deprem["depth"])
                saat = ham_saatler[0] if ham_saatler else "Bilinmiyor"
                lat = ilk_deprem['geojson']['coordinates'][1]
                lng = ilk_deprem['geojson']['coordinates'][0]
                maps_link = f"https://www.google.com/maps?q={lat},{lng}"

                mesaj = (
                    f"🔔 <b>YENİ DEPREM BİLDİRİMİ</b>\n\n"
                    f"📍 <b>Yer:</b> {ilk_deprem['title']}\n"
                    f"📊 <b>Büyüklük:</b> <b>{mag}</b>\n"
                    f"📉 <b>Derinlik:</b> {ilk_deprem['depth']} km\n"
                    f"⏰ <b>Saat:</b> {saat}\n"
                    f"🚦 <b>Analiz:</b> {risk['status']}\n\n"
                    f"📍 <a href='{maps_link}'>Google Haritalarda Gör</a>"
                )
                telegram_gonder(mesaj)
                LAST_NOTIFIED_ID[0] = d_id

            for i in range(len(api_data["result"])):
                q = api_data["result"][i]
                q["custom_hour"] = ham_saatler[i] if i < len(ham_saatler) else "00:00:00"
                q["risk_analysis"] = sismik_risk_etiketi(q["mag"], q["depth"])
        
        return jsonify(api_data)
    except Exception as e:
        return jsonify({"result": [], "error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

