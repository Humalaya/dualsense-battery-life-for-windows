import time
import os
import threading
from collections import deque

import keyboard
from pydualsense import pydualsense
from pydualsense.enums import BatteryState

from battery_notification import BatteryNotificationUI

# =========================
# AYARLAR
# =========================
LOG_DOSYASI = "sarj_gecmisi.txt"
GUNCELLEME_ARALIGI = 5
LOG_ARALIGI = 30
MAX_KAYIT = 500
MAX_LOG_YASI = 60 * 60 * 12

HOTKEY_DURUM = "F8"
HOTKEY_TEMIZLE = "F9"
HOTKEY_CIKIS = "esc"

BILDIRIM_SURESI = 5000
DEBUG = True

UYARI_ESIKLERI = [30, 15, 5]


def terminali_temizle():
    os.system("cls" if os.name == "nt" else "clear")


class DualSenseMonitor:
    def __init__(self):
        self.ds = pydualsense()
        self.bagli = False

        self.sarj_gecmisi = deque(maxlen=MAX_KAYIT)
        self.son_log_zamani = 0

        self.son_pil = None
        self.son_durum = None

        self.lock = threading.Lock()
        self.uyari_verildi = set()
        self.bekleyen_uyari = None

        self.log_yukle()

    def baglan(self):
        if not self.bagli:
            self.ds.init()
            self.bagli = True

    def kapat(self):
        try:
            self.ds.close()
        except Exception:
            pass
        self.bagli = False

    def pil_seviyesi_kategori(self, pil):
        if pil >= 80:
            return "tam"
        elif 30 < pil < 80:
            return "yarim"
        elif 5 < pil <= 30:
            return "az"
        else:
            return "bos"

    def log_kaydet(self, zaman, pil, durum):
        try:
            with open(LOG_DOSYASI, "a", encoding="utf-8") as f:
                f.write(f"{zaman},{pil},{int(durum)}\n")
        except Exception:
            pass

    def log_yukle(self):
        if not os.path.exists(LOG_DOSYASI):
            return

        try:
            with open(LOG_DOSYASI, "r", encoding="utf-8") as f:
                for line in f:
                    try:
                        parcalar = line.strip().split(",")
                        if len(parcalar) >= 3:
                            zaman = float(parcalar[0])
                            pil = int(parcalar[1])
                            durum = int(parcalar[2])
                            self.sarj_gecmisi.append((zaman, pil, durum))
                            self.son_log_zamani = max(self.son_log_zamani, zaman)
                    except Exception:
                        continue
        except Exception:
            pass

    def log_temizle(self):
        with self.lock:
            self.sarj_gecmisi.clear()
            self.son_log_zamani = 0
            try:
                with open(LOG_DOSYASI, "w", encoding="utf-8") as f:
                    f.write("")
            except Exception:
                pass

    def loga_ekle(self, zaman, pil, durum, zorla=False):
        if zorla or (zaman - self.son_log_zamani >= LOG_ARALIGI):
            self.sarj_gecmisi.append((zaman, pil, int(durum)))
            self.log_kaydet(zaman, pil, durum)
            self.son_log_zamani = zaman

    def eski_kayitlari_ayikla(self, simdi):
        temiz = deque(maxlen=MAX_KAYIT)
        for zaman, pil, durum in self.sarj_gecmisi:
            if simdi - zaman <= MAX_LOG_YASI:
                temiz.append((zaman, pil, durum))
        self.sarj_gecmisi = temiz

    def pil_ve_durum_oku(self):
        pil = self.ds.battery.Level
        durum = self.ds.battery.State
        return pil, durum

    def enum_adi(self, durum):
        try:
            return BatteryState(durum).name
        except Exception:
            return str(durum)

    def durum_metni(self, durum, pil):
        if durum == BatteryState.POWER_SUPPLY_STATUS_CHARGING:
            return "Şarj oluyor"
        if durum == BatteryState.POWER_SUPPLY_STATUS_FULL or pil >= 100:
            return "Tam dolu"
        if pil <= 15:
            return "Pil kritik"
        return "Kablosuz mod"

    def baglanti_metni(self, durum, pil):
        if durum == BatteryState.POWER_SUPPLY_STATUS_CHARGING:
            return "USB bağlı"
        if durum == BatteryState.POWER_SUPPLY_STATUS_FULL or pil >= 100:
            return "USB bağlı"
        return "Bluetooth"

    def zamani_formatla(self, saniye):
        saniye = max(0, int(saniye))
        saat = saniye // 3600
        dakika = (saniye % 3600) // 60

        if saat > 0:
            return f"{saat} sa {dakika} dk"
        return f"{dakika} dk"

    def farkli_pil_noktalari(self, kayitlar):
        sonuc = []
        son_pil = None
        for zaman, pil, durum in kayitlar:
            if pil != son_pil:
                sonuc.append((zaman, pil, durum))
                son_pil = pil
        return sonuc

    def sarj_tahmini_hesapla(self, pil):
        sarj_kayitlari = [k for k in self.sarj_gecmisi if k[2] == int(BatteryState.POWER_SUPPLY_STATUS_CHARGING)]

        if len(sarj_kayitlari) < 2:
            return "Tahmin için veri toplanıyor"

        farkli = self.farkli_pil_noktalari(sarj_kayitlari)
        if len(farkli) < 2:
            return "Şarj verisi toplanıyor"

        ilk_zaman, ilk_pil, _ = farkli[0]
        son_zaman, son_pil, _ = farkli[-1]

        toplam_sure = son_zaman - ilk_zaman
        toplam_artis = son_pil - ilk_pil

        if toplam_sure <= 0 or toplam_artis <= 0:
            return "Şarj tahmini hesaplanamadı"

        saniye_basi_yuzde = toplam_sure / toplam_artis
        kalan_yuzde = 100 - pil
        kalan_saniye = kalan_yuzde * saniye_basi_yuzde

        return f"Tahmini dolum: {self.zamani_formatla(kalan_saniye)}"

    def bitis_tahmini_hesapla(self, pil):
        pil_kayitlari = [
            k for k in self.sarj_gecmisi
            if k[2] not in (
                int(BatteryState.POWER_SUPPLY_STATUS_CHARGING),
                int(BatteryState.POWER_SUPPLY_STATUS_FULL),
            )
        ]

        if len(pil_kayitlari) < 2:
            return "Tahmin için veri toplanıyor"

        farkli = self.farkli_pil_noktalari(pil_kayitlari)
        if len(farkli) < 2:
            return "Kullanım verisi toplanıyor"

        ilk_zaman, ilk_pil, _ = farkli[0]
        son_zaman, son_pil, _ = farkli[-1]

        toplam_sure = son_zaman - ilk_zaman
        harcanan_pil = ilk_pil - son_pil

        if toplam_sure <= 0 or harcanan_pil <= 0:
            return "Kullanım tahmini hesaplanamadı"

        saniye_basi_yuzde = toplam_sure / harcanan_pil
        kalan_saniye = pil * saniye_basi_yuzde

        return f"Tahmini kullanım: {self.zamani_formatla(kalan_saniye)}"

    def bluetooth_uyari_kontrol(self, pil, durum):
        if durum == BatteryState.POWER_SUPPLY_STATUS_CHARGING:
            self.uyari_verildi.clear()
            return None

        if durum == BatteryState.POWER_SUPPLY_STATUS_FULL or pil >= 100:
            return None

        for esik in UYARI_ESIKLERI:
            if pil <= esik and esik not in self.uyari_verildi:
                self.uyari_verildi.add(esik)
                if esik == 30:
                    return "Pil düşük (%30)"
                elif esik == 15:
                    return "Pil çok düşük (%15)"
                elif esik == 5:
                    return "Pil kritik (%5)"
        return None

    def guncelle(self):
        with self.lock:
            try:
                self.baglan()
                pil, durum = self.pil_ve_durum_oku()
                simdi = time.time()

                degisim_var = (pil != self.son_pil) or (durum != self.son_durum)

                self.loga_ekle(simdi, pil, durum, zorla=degisim_var)
                self.eski_kayitlari_ayikla(simdi)

                uyari = self.bluetooth_uyari_kontrol(pil, durum)
                if uyari:
                    self.bekleyen_uyari = uyari

                self.son_pil = pil
                self.son_durum = durum

            except Exception:
                self.kapat()

    def anlik_durum_verisi(self):
        with self.lock:
            self.baglan()
            pil, durum = self.pil_ve_durum_oku()

            if durum == BatteryState.POWER_SUPPLY_STATUS_CHARGING:
                tahmin = self.sarj_tahmini_hesapla(pil)
            elif durum == BatteryState.POWER_SUPPLY_STATUS_FULL or pil >= 100:
                tahmin = "Tahmini dolum: 0 dk"
            else:
                tahmin = self.bitis_tahmini_hesapla(pil)

            return {
                "pil": pil,
                "durum": durum,
                "durum_metni": self.durum_metni(durum, pil),
                "baglanti_metni": self.baglanti_metni(durum, pil),
                "tahmin": tahmin,
                "kayit_sayisi": len(self.sarj_gecmisi),
                "enum_adi": self.enum_adi(durum),
            }

    def bekleyen_uyariyi_al(self):
        with self.lock:
            uyari = self.bekleyen_uyari
            self.bekleyen_uyari = None
            return uyari


def main():
    monitor = DualSenseMonitor()
    ui = BatteryNotificationUI(monitor, bildirim_suresi=BILDIRIM_SURESI)

    if DEBUG:
        terminali_temizle()
        print("=" * 54)
        print("🎮 DUALSENSE HOTKEY BİLDİRİM SİSTEMİ")
        print("=" * 54)
        print(f"{HOTKEY_DURUM}  -> bildirim aç")
        print(f"{HOTKEY_TEMIZLE}  -> log temizle")
        print(f"{HOTKEY_CIKIS} -> çıkış")
        print(f"Log dosyası: {os.path.abspath(LOG_DOSYASI)}")
        print("=" * 54)

    keyboard.add_hotkey(HOTKEY_DURUM, lambda: ui.root.after(0, ui.durum_goster))
    keyboard.add_hotkey(HOTKEY_TEMIZLE, lambda: (monitor.log_temizle(), ui.root.after(0, ui.log_temizlendi_bildirimi)))
    keyboard.add_hotkey(HOTKEY_CIKIS, lambda: ui.root.after(0, ui.root.quit))

    def arka_plan_guncelle():
        while True:
            try:
                monitor.guncelle()
                uyari = monitor.bekleyen_uyariyi_al()
                if uyari:
                    ui.root.after(0, ui.durum_goster)
                time.sleep(GUNCELLEME_ARALIGI)
            except Exception:
                time.sleep(GUNCELLEME_ARALIGI)

    thread = threading.Thread(target=arka_plan_guncelle, daemon=True)
    thread.start()

    ui.root.mainloop()
    monitor.kapat()


if __name__ == "__main__":
    main()