import json
import os


def yukle(dosya, default):
    """
    JSON dosyasını güvenli şekilde okur.
    Dosya yoksa veya bozuksa default döner.
    """
    if not os.path.exists(dosya):
        return default
    try:
        with open(dosya, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"❌ JSON bozuk: {dosya}")
        return default
    except Exception as e:
        print(f"❌ Dosya okunamadı: {dosya} → {e}")
        return default

def kaydet(dosya, veri):
    """
    JSON dosyasını güvenli şekilde yazar.
    Gerekirse klasörü otomatik oluşturur.
    """
    klasor = os.path.dirname(dosya)
    if klasor:
        os.makedirs(klasor, exist_ok=True)
    try:
        with open(dosya, "w", encoding="utf-8") as f:
            json.dump(veri, f, ensure_ascii=False, indent=2)

    except Exception as e:
        print(f"❌ Dosya yazılamadı: {dosya} → {e}")
