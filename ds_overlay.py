import tkinter as tk
from pydualsense import pydualsense
from pydualsense.enums import BatteryState
import winsound
import screeninfo

from icons import TAM_B64, YARIM_B64, AZ_B64, BOS_B64

# --- AYARLAR ---
GUNCELLEME_SURESI = 3000 # Kontrolü 3 saniyeye düşürdük (daha hızlı tepki)
GIZLEME_SURESI = 7000 
FADE_HIZI = 50

class DualSenseHUD:
    def __init__(self):
        self.root = tk.Tk()
        self.ds = pydualsense()
        
        # HAFIZA SİSTEMİ
        self.eski_pil = -1
        self.eski_sarj_ham_durum = None # Enum değerini direkt tutacağız
        self.baglanti_durumu = False
        self.ilk_acilis = True
        self.gizleme_id = None
        
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', 0.0)
        self.root.configure(bg='#1A1A1A')

        try:
            monitor = screeninfo.get_monitors()[0]
            self.root.geometry(f"+{monitor.width - 220}+50")
        except:
            self.root.geometry("+1600+50")

        self.ikon_tam = tk.PhotoImage(data=TAM_B64)
        self.ikon_yarim = tk.PhotoImage(data=YARIM_B64)
        self.ikon_az = tk.PhotoImage(data=AZ_B64)
        self.ikon_bos = tk.PhotoImage(data=BOS_B64)

        self.label = tk.Label(self.root, text="", font=("Consolas", 11, "bold"), bg="#1A1A1A", fg="white", pady=5)
        self.label.pack()

        self.dongu()
        self.root.mainloop()

    def fade_in(self, alpha=0.0):
        if alpha < 0.9:
            alpha += 0.1
            self.root.attributes('-alpha', alpha)
            self.root.after(FADE_HIZI, self.fade_in, alpha)

    def fade_out(self, alpha=0.9):
        if alpha > 0.0:
            alpha -= 0.1
            self.root.attributes('-alpha', alpha)
            self.root.after(FADE_HIZI, self.fade_out, alpha)

    def gizle(self):
        self.fade_out()
        self.gizleme_id = None

    def dongu(self):
        try:
            # 1. Ham Verileri Çek
            if not self.baglanti_durumu:
                self.ds.init()
                self.baglanti_durumu = True

            pil = self.ds.battery.Level
            sarj_ham = self.ds.battery.State # Enum: Charging, Discharging, Full vb.
            
            # Şarjda mı kontrolü (Charging veya Full ise True)
            su_an_sarj = (sarj_ham == BatteryState.POWER_SUPPLY_STATUS_CHARGING or 
                         sarj_ham == BatteryState.POWER_SUPPLY_STATUS_FULL)

            # 2. Değişim Analizi
            # Herhangi bir durum değişikliği (pil değişimi, kablo takılması VEYA çıkarılması)
            durum_degisti = (pil != self.eski_pil) or (sarj_ham != self.eski_sarj_ham_durum)
            
            # 3. Görsel Hazırlık
            secilen_ikon = self.ikon_tam
            text, color = f"%{pil} ", "white"

            if su_an_sarj:
                text, color = f"⚡ %{pil} Şarj Oluyor", "#F1C40F"
                secilen_ikon = self.ikon_tam 
            elif pil >= 70: secilen_ikon = self.ikon_tam
            elif pil >= 45: secilen_ikon = self.ikon_yarim
            elif pil >= 15: secilen_ikon = self.ikon_az
            else:
                text, color = f"⚠️ %{pil} PİL KRİTİK!", "#E74C3C"
                secilen_ikon = self.ikon_bos

            self.label.config(image=secilen_ikon, text=text, fg=color, compound="top")
            
            # 4. Tetikleme Kuralları
            kritik = (pil <= 15 and not su_an_sarj)
            
            if durum_degisti or self.ilk_acilis or kritik:
                # Sadece Şarj TAKILDIĞINDA veya ilk bağlantıda ses çal
                kablo_takildi = (sarj_ham == BatteryState.POWER_SUPPLY_STATUS_CHARGING and 
                                self.eski_sarj_ham_durum != BatteryState.POWER_SUPPLY_STATUS_CHARGING)
                
                if self.ilk_acilis or kablo_takildi or (kritik and self.eski_pil > 15):
                    winsound.PlaySound("SystemNotification", winsound.SND_ALIAS)

                # Paneli uyandır
                if self.root.attributes('-alpha') < 0.2:
                    self.fade_in()

                # Sayaç yönetimi
                if self.gizleme_id:
                    self.root.after_cancel(self.gizleme_id)
                
                if not kritik:
                    self.gizleme_id = self.root.after(GIZLEME_SURESI, self.gizle)

                self.ilk_acilis = False

            # Hafızayı Güncelle
            self.eski_pil = pil
            self.eski_sarj_ham_durum = sarj_ham

        except Exception:
            # Hata varsa (Bağlantı koptuysa)
            if self.baglanti_durumu:
                self.baglanti_durumu = False
                self.eski_sarj_ham_durum = None
                self.label.config(image='', text="🎮 Bağlantı Koptu", fg="#95A5A6")
                self.fade_in()
                if self.gizleme_id: self.root.after_cancel(self.gizleme_id)
                self.gizleme_id = self.root.after(4000, self.gizle)

            try: self.ds.close()
            except: pass

        self.root.after(GUNCELLEME_SURESI, self.dongu)

if __name__ == "__main__":
    DualSenseHUD()