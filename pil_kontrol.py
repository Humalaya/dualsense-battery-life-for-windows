import time
import os
from pydualsense import pydualsense
from pydualsense.enums import BatteryState

def terminali_temizle():
    # Windows için 'cls', Linux/Mac için 'clear'
    os.system('cls' if os.name == 'nt' else 'clear')

def pil_izleyici():
    ds = pydualsense()
    
    try:
        ds.init()
        print("✅ DualSense bağlantısı başarılı!")
        time.sleep(1)
        
        while True:
            terminali_temizle()
            
            pil = ds.battery.Level
            durum = ds.battery.State
            
            # Şarj durumuna göre metin belirle
            if durum == BatteryState.POWER_SUPPLY_STATUS_CHARGING:
                durum_metni = "⚡ Şarj Oluyor"
            elif durum == BatteryState.POWER_SUPPLY_STATUS_FULL:
                durum_metni = "🔋 Tam Dolu"
            else:
                durum_metni = "🔌 Deşarj Oluyor"

            print("="*30)
            print(f"🎮 DUALSENSE DURUMU")
            print("="*30)
            print(f"🔋 Pil Yüzdesi: %{pil}")
            print(f"ℹ️  Durum      : {durum_metni}")
            print("="*30)
            print("\n(Çıkmak için Ctrl+C tuşlarına basın)")
            # Mevcut satırın altına ekle
            print(f"DEBUG - Ham Pil Değeri: {ds.battery.Level}")
            print(f"DEBUG - Ham Şarj Durumu: {ds.battery.State}")
            # Her 2 saniyede bir güncelle
            time.sleep(2)
            
    except Exception as e:
        print(f"❌ Hata: {e}")
        print("Kontrolcünün bağlı olduğundan emin olun.")
    finally:
        ds.close()

if __name__ == "__main__":
    pil_izleyici()