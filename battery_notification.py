import tkinter as tk
from pydualsense.enums import BatteryState
from icons import TAM_B64, YARIM_B64, AZ_B64, BOS_B64


class BatteryNotificationUI:
    def __init__(self, monitor, bildirim_suresi=5000):
        self.monitor = monitor
        self.bildirim_suresi = bildirim_suresi

        self.root = tk.Tk()
        self.root.withdraw()

        self.popup = None
        self.auto_close_id = None

        # ORJİNAL ICONLAR
        self.ikon_tam_orj = tk.PhotoImage(data=TAM_B64)
        self.ikon_yarim_orj = tk.PhotoImage(data=YARIM_B64)
        self.ikon_az_orj = tk.PhotoImage(data=AZ_B64)
        self.ikon_bos_orj = tk.PhotoImage(data=BOS_B64)

        # 🔥 AUTO SCALE
        self.ikon_tam = self.scale_icon(self.ikon_tam_orj)
        self.ikon_yarim = self.scale_icon(self.ikon_yarim_orj)
        self.ikon_az = self.scale_icon(self.ikon_az_orj)
        self.ikon_bos = self.scale_icon(self.ikon_bos_orj)

        # ANİMASYON
        self.animasyon_aktif = False
        self.animasyon_index = 0
        self.animasyon_dizi = ["az", "yarim", "tam"]

    # =========================
    # KATEGORİ
    # =========================
    def pil_seviyesi_kategori(self, pil):
        if pil >= 80:
            return "tam"
        elif 30 < pil < 80:
            return "yarim"
        elif 5 < pil <= 30:
            return "az"
        else:
            return "bos"

    def kategoriye_gore_ikon(self, kategori):
        if kategori == "tam":
            return self.ikon_tam
        elif kategori == "yarim":
            return self.ikon_yarim
        elif kategori == "az":
            return self.ikon_az
        return self.ikon_bos

    def ikon_sec(self, pil, durum):
        if durum == BatteryState.POWER_SUPPLY_STATUS_CHARGING:
            kategori = self.animasyon_dizi[self.animasyon_index]
        else:
            kategori = self.pil_seviyesi_kategori(pil)

        return self.kategoriye_gore_ikon(kategori)

    # =========================
    # RENK
    # =========================
    def renk_sec(self, pil, durum):
        if durum == BatteryState.POWER_SUPPLY_STATUS_CHARGING:
            return {"bg": "#0f1115", "card": "#171a21", "main": "#ffd166", "sub": "#fff0c2", "muted": "#bfae7a", "line": "#272c36"}
        if pil <= 15:
            return {"bg": "#0f1115", "card": "#171a21", "main": "#ff7b72", "sub": "#ffd6d2", "muted": "#b7a19f", "line": "#272c36"}
        return {"bg": "#0f1115", "card": "#171a21", "main": "#f5f7fa", "sub": "#d8dee9", "muted": "#9aa4b2", "line": "#272c36"}

    # =========================
    # ANİMASYON
    # =========================
    def animasyon_guncelle(self):
        self.animasyon_index = (self.animasyon_index + 1) % len(self.animasyon_dizi)

    def sarj_animasyonu(self):
        if not self.popup or not self.animasyon_aktif:
            return

        try:
            veri = self.monitor.anlik_durum_verisi()
            if veri["durum"] != BatteryState.POWER_SUPPLY_STATUS_CHARGING:
                self.animasyon_aktif = False
                return
        except:
            return

        self.animasyon_guncelle()

        pil = veri["pil"]
        self.icon_label.configure(image=self.ikon_sec(pil, veri["durum"]))

        self.popup.after(350, self.sarj_animasyonu)

    # =========================
    # UI
    # =========================
    def popup_kapat(self):
        if self.popup:
            self.popup.destroy()
            self.popup = None
            self.animasyon_aktif = False
    def scale_icon(self, img, max_w=120, max_h=90):
        w = img.width()
        h = img.height()

        scale_w = max(1, w // max_w)
        scale_h = max(1, h // max_h)

        scale = max(scale_w, scale_h)

        return img.subsample(scale, scale)
    def durum_goster(self):
        try:
            veri = self.monitor.anlik_durum_verisi()
        except:
            return

        self.popup_kapat()

        self.popup = tk.Toplevel(self.root)
        self.popup.overrideredirect(True)
        self.popup.attributes("-topmost", True)

        pil = veri["pil"]
        renk = self.renk_sec(pil, veri["durum"])

        self.popup.configure(bg=renk["bg"])

        # 🔥 DAHA DENGELİ BOYUT
        width = 500
        height = 170

        x = self.popup.winfo_screenwidth() - width - 20
        y = 40

        self.popup.geometry(f"{width}x{height}+{x}+{y}")

        outer = tk.Frame(self.popup, bg=renk["bg"], padx=8, pady=8)
        outer.pack(fill="both", expand=True)

        card = tk.Frame(outer, bg=renk["card"], padx=15, pady=12)
        card.pack(fill="both", expand=True)

        content = tk.Frame(card, bg=renk["card"])
        content.pack(fill="both", expand=True)

        # 🔥 SOL ALAN DÜZELTME
        left = tk.Frame(content, bg=renk["card"], width=150, height=110)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        right = tk.Frame(content, bg=renk["card"])
        right.pack(side="left", fill="both", expand=True, padx=(15, 0))

        self.animasyon_aktif = veri["durum"] == BatteryState.POWER_SUPPLY_STATUS_CHARGING

        self.icon_label = tk.Label(
            left,
            image=self.ikon_sec(pil, veri["durum"]),
            bg=renk["card"]
        )
        self.icon_label.pack(expand=True)

        percent = tk.Label(
            right,
            text=f"%{pil}",
            font=("Segoe UI", 24, "bold"),
            fg=renk["main"],
            bg=renk["card"]
        )
        percent.pack(anchor="w")

        status = tk.Label(
            right,
            text=veri["durum_metni"],
            font=("Segoe UI", 11),
            fg=renk["sub"],
            bg=renk["card"]
        )
        status.pack(anchor="w")

        tahmin = tk.Label(
            right,
            text=veri["tahmin"],
            font=("Segoe UI", 10),
            fg=renk["muted"],
            bg=renk["card"]
        )
        tahmin.pack(anchor="w", pady=(6, 0))

        footer = tk.Label(
            right,
            text=veri["baglanti_metni"],
            font=("Segoe UI", 9),
            fg=renk["muted"],
            bg=renk["card"]
        )
        footer.pack(anchor="w", pady=(6, 0))

        self.popup.after(self.bildirim_suresi, self.popup_kapat)

        if self.animasyon_aktif:
            self.popup.after(350, self.sarj_animasyonu)

    def log_temizlendi_bildirimi(self):
        self.popup_kapat()

        self.popup = tk.Toplevel(self.root)
        self.popup.overrideredirect(True)
        self.popup.attributes("-topmost", True)

        self.popup.geometry("320x100+1000+40")

        label = tk.Label(self.popup, text="Log temizlendi", font=("Segoe UI", 12))
        label.pack(expand=True)

        self.popup.after(2000, self.popup_kapat)