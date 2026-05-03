import socket
import sys
from datetime import datetime

def scan_target():
    print("\n" + "="*50)
    print("   HAXK ULTIMATE PORT SCANNER v2.1")
    print("="*50)

    # Site adını temizle (http/https varsa temizler)
    target = input("Hedef Site (örn: google.com): ").strip().replace("http://", "").replace("https://", "").split("/")[0]

    try:
        # Site isminden IP'yi çek
        target_ip = socket.gethostbyname(target)
        print(f"\n[+] Hedef Site: {target}")
        print(f"[+] Hedef IP:   {target_ip}")
        print(f"[*] Tarama Başladı: {datetime.now().strftime('%H:%M:%S')}")
        print("-" * 50)
    except socket.gaierror:
        print("\n[-] HATA: Site adresi çözülemedi! İnternetini veya siteyi kontrol et.")
        return

    # Taranacak en popüler portlar
    # Eğer bunlar da boş dönerse site her şeyi kapatmış demektir
    ports = [21, 22, 25, 53, 80, 110, 443, 445, 3306, 3389, 8080]
    
    found_any = False

    for port in ports:
        # Soket ayarları
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.5) # Cevap verme süresini biraz artırdık
        
        # Bağlantı denemesi
        result = s.connect_ex((target_ip, port))
        
        if result == 0:
            try:
                service = socket.getservbyport(port)
            except:
                service = "Bilinmiyor"
            print(f"[!] PORT AÇIK: {port:<5} | Servis: {service}")
            found_any = True
        
        s.close()

    if not found_any:
        print("\n[-] Hiç açık port bulunamadı.")
        print("[*] Tavsiye: Hedef site Firewall (Güvenlik Duvarı) kullanıyor olabilir.")
    
    print("-" * 50)
    print(f"[*] Tarama Bitti: {datetime.now().strftime('%H:%M:%S')}")

if __name__ == "__main__":
    try:
        scan_target()
    except KeyboardInterrupt:
        print("\n[!] Tarama durduruldu.")
        sys.exit()
