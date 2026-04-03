# DualSense Battery Monitor & HUD

DualSense (PS5) kontrolcünüzün pil seviyesini Windows üzerinde gerçek zamanlı olarak takip etmenizi sağlayan, minimalist ve akıllı bir arayüz (HUD) uygulamasıdır.

## Özellikler

  * **Akıllı Görünmezlik (Ghost Mode):** Panel sadece pil seviyesi değiştiğinde, şarj takıldığında veya bağlantı koptuğunda görünür. Diğer zamanlarda ekranınızı kirletmez.
  * **Dinamik HUD:** Sağ üst köşede her zaman en üstte duran (Always-on-Top), çerçevesiz minimalist panel.
  * **AI Tasarımı İkonlar:** Pil durumuna göre renk değiştiren (Yeşil, Sarı, Turuncu, Kırmızı) 4 farklı minimalist ikon.
  * **Sesli Bildirimler:** Şarj takıldığında veya pil kritik seviyeye (%15) düştüğünde Windows sistem sesiyle uyarı verir.
  * **Kritik Pil Koruması:** Pil %15'in altına düştüğünde, siz şarja takana kadar panel ekranda sabit kalarak sizi uyarır.
  * **Otomatik Bağlantı:** Kontrolcü açıldığı veya kapandığı anda durumu otomatik algılar ve yeniden bağlanır.

## Proje Yapısı

  * `ds_overlay.py`: Ana uygulama mantığı, HUD yönetimi ve Ghost Mode sistemi.
  * `icons.py`: AI tarafından tasarlanmış, Base64 formatında gömülü ikon verileri.
  * `dist/`: Derlenmiş `.exe` dosyasının bulunduğu klasör.

## Tasarım Notları

> [\!IMPORTANT]  
> Bu projedeki tüm batarya ikonları **yapay zeka** tarafından minimalist bir tasarım diliyle oluşturulmuştur. Panel arka planı için PS5 ekosistemine uygun koyu gri (`#1A1A1A`) tercih edilmiştir.
