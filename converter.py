import base64

resimler = ["pil_tam.png", "pil_yarim.png", "pil_az.png", "pil_bos.png"]

for resim in resimler:
    try:
        with open(resim, "rb") as f:
            b64_kodu = base64.b64encode(f.read()).decode('utf-8')
            print(f"{resim.split('.')[0].upper()}_B64 = '{b64_kodu}'\n")
    except FileNotFoundError:
        print(f"Hata: {resim} bulunamadı!")