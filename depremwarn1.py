import requests
import tkinter as tk
from datetime import datetime
import threading
import time
import re

KANDILLI_URL = "https://api.orhanaydogdu.com.tr/deprem/kandilli/live"
CHECK_INTERVAL = 60  # saniye

class DepremTakipApp:
    def __init__(self, master):
        self.master = master
        master.title("🌍 Kandilli Deprem Takip")
        master.geometry("600x380")

        self.label_baslik = tk.Label(master, text="🔴 Son Deprem", font=("Helvetica", 16, "bold"))
        self.label_baslik.pack(pady=10)

        self.label_icerik = tk.Label(master, text="Yükleniyor...", font=("Helvetica", 12), justify="left")
        self.label_icerik.pack(pady=10)

        self.label_sure = tk.Label(master, text="", font=("Helvetica", 10), fg="gray")
        self.label_sure.pack(pady=5)

        self.label_fark = tk.Label(master, text="", font=("Helvetica", 10), fg="blue")
        self.label_fark.pack(pady=5)

        self.label_uyari = tk.Label(master, text="", font=("Helvetica", 12, "bold"), fg="red")
        self.label_uyari.pack(pady=10)

        self.last_quake_id = None

        self.update_thread = threading.Thread(target=self.check_for_updates, daemon=True)
        self.update_thread.start()

    def fetch_data(self):
        try:
            resp = requests.get(KANDILLI_URL)
            resp.raise_for_status()
            return resp.json()["result"]
        except:
            return []

    def get_parantez_ici(self, title):
        # Parantez içindekini bul (varsa)
        m = re.search(r"\((.*?)\)", title)
        if m:
            return m.group(1).strip()
        return None

    def format_quake(self, eq):
        dt = datetime.strptime(eq["date"], "%Y.%m.%d %H:%M:%S")
        parantez_ici = self.get_parantez_ici(eq["title"])
        yer = eq["title"]
        if parantez_ici:
            yer += f"\n🔹 Bölge: ({parantez_ici})"
        return f"Tarih: {dt.strftime('%Y-%m-%d %H:%M:%S')}\n" \
               f"Büyüklük: {eq['mag']} ML\n" \
               f"Derinlik: {eq['depth']} km\n" \
               f"Yer: {yer}"

    def check_for_updates(self):
        while True:
            data = self.fetch_data()
            if data and len(data) > 0:
                current = data[0]
                current_dt = datetime.strptime(current["date"], "%Y.%m.%d %H:%M:%S")
                current_bolge = self.get_parantez_ici(current["title"])

                # Aynı parantez içi bölgedeki önceki depremleri topla
                same_region_quakes = []
                for quake in data[1:]:
                    quake_bolge = self.get_parantez_ici(quake["title"])
                    if quake_bolge == current_bolge and quake_bolge is not None:
                        same_region_quakes.append(quake)
                    if len(same_region_quakes) >= 3:
                        break

                # Süre farkı hesaplama (aynı parantez içi bölgedeki en yakın önceki deprem)
                previous_same_region_quake = None
                for quake in data[1:]:
                    quake_bolge = self.get_parantez_ici(quake["title"])
                    if quake_bolge == current_bolge and quake_bolge is not None:
                        previous_same_region_quake = quake
                        break

                if previous_same_region_quake:
                    prev_dt = datetime.strptime(previous_same_region_quake["date"], "%Y.%m.%d %H:%M:%S")
                    delta = current_dt - prev_dt
                    mins_between_quakes = int(delta.total_seconds() // 60)
                    fark_text = f"🕒 Aynı bölgede önceki depreme göre fark: {mins_between_quakes} dakika"
                else:
                    fark_text = "⛔ Aynı bölgede önceki deprem bulunamadı."

                self.label_fark.config(text=fark_text)

                # Büyüklük artışı kontrolü (son 3 depremde artış varsa uyarı ver)
                if same_region_quakes:
                    son_depremler = [current] + same_region_quakes
                    son_depremler.sort(key=lambda x: datetime.strptime(x["date"], "%Y.%m.%d %H:%M:%S"))
                    buyuklukler = [float(q["mag"]) for q in son_depremler]

                    artis_var = all(x < y for x, y in zip(buyuklukler, buyuklukler[1:]))

                    if artis_var and len(buyuklukler) >= 2:
                        self.label_uyari.config(text="⚠️ Aynı bölgede art arda büyüyen mikro depremler var!")
                    else:
                        self.label_uyari.config(text="")
                else:
                    self.label_uyari.config(text="")

                if current["date"] != self.last_quake_id:
                    self.last_quake_id = current["date"]
                    self.label_icerik.config(text=self.format_quake(current))
                    self.label_sure.config(text="🟢 Yeni deprem algılandı!")
                else:
                    self.label_sure.config(text="🔄 Yeni deprem yok.")

            else:
                self.label_icerik.config(text="❌ Veri alınamadı.")
                self.label_fark.config(text="")
                self.label_uyari.config(text="")

            time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    root = tk.Tk()
    app = DepremTakipApp(root)
    root.mainloop()
