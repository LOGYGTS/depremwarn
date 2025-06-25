<!DOCTYPE html>
<html lang="tr">
<head>
  <meta charset="UTF-8">
  <title>🌍 Deprem Takip</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: #f4f4f4;
      color: #333;
      margin: 0;
      padding: 0;
    }
    .container {
      max-width: 700px;
      margin: 40px auto;
      background: #fff;
      padding: 20px;
      border-radius: 12px;
      box-shadow: 0 0 15px rgba(0,0,0,0.2);
    }
    h1 {
      text-align: center;
    }
    .menu {
      text-align: center;
      margin-bottom: 20px;
    }
    .menu a {
      text-decoration: none;
      background: #3498db;
      color: white;
      padding: 10px 20px;
      border-radius: 6px;
      margin: 0 5px;
    }
    .uyari {
      margin-top: 15px;
      padding: 10px;
      border-radius: 6px;
      display: none;
      font-weight: bold;
    }
    .ok {
      background-color: #2ecc71;
      color: white;
    }
    .kritik {
      background-color: #e74c3c;
      color: white;
    }
    #map {
      height: 300px;
      margin-top: 20px;
      border-radius: 10px;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>🌍 Kandilli Deprem Takip</h1>

    <div class="menu">
      <a href="/onceki">📜 Önceki Depremler</a>
    </div>

    <div id="bilgi" class="deprem-info">Yükleniyor...</div>
    <div id="uyari" class="uyari"></div>
    <div id="map"></div>
  </div>

  <script>
    let map;

    function haritayiGuncelle(lat, lon, yer, mag) {
      if (!map) {
        map = L.map('map').setView([lat, lon], 7);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          attribution: '© OpenStreetMap'
        }).addTo(map);
      } else {
        map.setView([lat, lon], 7);
      }

      L.marker([lat, lon]).addTo(map)
        .bindPopup(`<b>${yer}</b><br>💥 Büyüklük: ${mag}`)
        .openPopup();
    }

    async function depremVerisi() {
      try {
        const res = await fetch("/api/deprem");
        const data = await res.json();

        if (data.error) {
          document.getElementById("bilgi").innerText = "Hata: " + data.error;
          return;
        }

        document.getElementById("bilgi").innerHTML = `
          📍 Yer: ${data.title}<br>
          📅 Tarih: ${data.date}<br>
          💥 Büyüklük: ${data.mag} ML<br>
          🌡️ Derinlik: ${data.depth} km<br>
          🕒 Önceki fark: ${data.fark}
        `;

        const uyari = document.getElementById("uyari");

        if (data.fark.includes("dk")) {
          const dakika = parseInt(data.fark);
          if (!isNaN(dakika) && dakika < 15) {
            uyari.style.display = "block";
            uyari.innerText = "⚠️ Uyarı: Aynı bölgede kısa sürede birden fazla deprem algılandı!";
            uyari.classList.remove("ok");
            uyari.classList.add("kritik");
          } else {
            uyari.style.display = "block";
            uyari.innerText = "🟢 Her şey normal.";
            uyari.classList.remove("kritik");
            uyari.classList.add("ok");
          }
        } else {
          uyari.style.display = "none";
        }

        haritayiGuncelle(data.lat, data.lon, data.title, data.mag);
      } catch (err) {
        document.getElementById("bilgi").innerText = "Veri alınamadı.";
      }
    }

    depremVerisi();
    setInterval(depremVerisi, 60000);
  </script>
</body>
</html>
