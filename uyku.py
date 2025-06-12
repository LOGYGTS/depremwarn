from flask import Flask
import threading
import time
import requests

app = Flask(__name__)

@app.route('/')
def home():
    return 'Sitem açık!'

# Kendini pingleyen fonksiyon
def self_ping():
    while True:
        try:
            print("Kendimi pinglemeye çalışıyorum...")
            requests.get("https://f5706b04-3c45-4192-84eb-d462cea12afe-00-2p2nkgz84oun1.sisko.replit.dev/")
        except:
            print("Ping başarısız")
        time.sleep(200)  # Her 10 dakikada bir pingle

# Thread başlat
threading.Thread(target=self_ping).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)