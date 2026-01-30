from flask import Flask, request, jsonify

from datetime import datetime
import json
import os
import hashlib
import uuid
import socket

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()


iptal_kuyrugu = []


app = Flask(__name__)

@app.route("/", methods=["GET"])
def root():
    return "OK"


# ================== DOSYA YOLLARI ==================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))   # C:\CevizAlti\garson_server
ROOT_DIR = os.path.dirname(BASE_DIR)                    # C:\CevizAlti

MENU_FILE = os.path.join(ROOT_DIR, "menu.json")
ADISYON_FILE = os.path.join(ROOT_DIR, "adisyonlar.json")
REVENUE_FILE = os.path.join(ROOT_DIR, "revenue.json")
USERS_FILE = os.path.join(ROOT_DIR, "users.json")
PRODUCTS_FILE = os.path.join(ROOT_DIR, "products.json")
SATIS_FILE = os.path.join(ROOT_DIR, "satis_detay.json")



# ================== YARDIMCI ==================
def load_json(path, default):
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_adisyonlar():
    return load_json(ADISYON_FILE, {})

# ================== LOGIN ==================
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    password = data.get("password")

    if not password:
        return jsonify({"ok": False, "msg": "Şifre yok"}), 400

    password_hash = hashlib.sha256(password.encode()).hexdigest()
    users = load_json(USERS_FILE, {})

    for username, u in users.items():
        if not u.get("aktif", True):
            continue

        if u.get("password") == password_hash:
            return jsonify({
                "ok": True,
                "kullanici": username,
                "rol": u.get("role", "user")
            }), 200

    return jsonify({"ok": False, "msg": "Şifre hatalı"}), 401

# ================== MENU ==================
@app.route("/menu", methods=["GET"])
def menu_getir():
    return jsonify(load_json(MENU_FILE, {})), 200

# ================== ADİSYONLAR (WINDOWS & APK) ==================
@app.route("/adisyonlar", methods=["GET"])
def adisyonlari_getir():
    try:
        with open(ADISYON_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data), 200
    except FileNotFoundError:
        return jsonify({}), 200

# ================== SİPARİŞ AL ==================
@app.route("/siparis", methods=["POST"])
def siparis_al():
    try:
        data = request.get_json(force=True)
    except:
        return jsonify({"hata": "JSON okunamadı"}), 400

    masa = str(data.get("masa", "")).strip()
    urunler = data.get("urunler", [])
    kullanici = data.get("kullanici", "Bilinmiyor")

    if not masa:
        return jsonify({"hata": "Masa bilgisi yok"}), 400

    if not isinstance(urunler, list) or len(urunler) == 0:
        return jsonify({"hata": "Ürün listesi boş"}), 400

    adisyonlar = get_adisyonlar()

    if masa not in adisyonlar:
        adisyonlar[masa] = {
            "id": uuid.uuid4().hex,   # 🔥 ADİSYON ID (YENİ)
            "masa": masa,
            "kullanici": kullanici,
            "urunler": []
        }

    for u in urunler:
        menu_id = str(u.get("menu_id", "")).strip()
        adet = int(u.get("adet", 1))

        if not menu_id:
            continue

        adisyonlar[masa]["urunler"].append({
            "id": uuid.uuid4().hex,
            "menu_id": menu_id,
            "adet": adet,
            "not": u.get("not", ""),
            "kullanici": kullanici,
            "zaman": datetime.now().strftime("%H:%M:%S"),
            "hazir": False,
            "bildirildi": False
        })


    save_json(ADISYON_FILE, adisyonlar)
    return jsonify({"ok": True}), 200


# ================== ADİSYONLAR ==================
@app.route("/siparisler", methods=["GET"])
def siparisleri_getir():
    adisyonlar = load_json(ADISYON_FILE, {})
    print("ADISYONLAR:", adisyonlar)
    menu = load_json(MENU_FILE, {})

    sonuc = {}

    for masa, adisyon in adisyonlar.items():
        liste = []

        for u in adisyon.get("urunler", []):
            menu_id = str(u.get("menu_id"))
            adet = int(u.get("adet", 1))

            if menu_id not in menu:
                continue

            menu_item = menu[menu_id]

            # ❌ mutfağa gönderilmeyecekse atla (içecekler dahil)
            if not menu_item.get("mutfak", True):
                continue

            liste.append({
            "id": u["id"],
            "menu_id": menu_id,      # 🔴 BUNU EKLE
            "ad": menu_item.get("ad"),
            "adet": adet,
            "fiyat": menu_item.get("fiyat", 0),
            "not": u.get("not", ""),
            "hazir": u.get("hazir", False),   # 🔥 TEK SATIR
        })


        if liste:
            sonuc[masa] = {
                "adisyon_id": adisyon.get("id"),
                "urunler": liste
            }
    return jsonify(sonuc), 200


# ================== SİPARİŞ HAZIR (MUTFAK) ==================
@app.route("/siparis_hazir", methods=["POST"])
def siparis_hazir():
    data = request.get_json(force=True)

    masa = data.get("masa")
    siparis_id = str(data.get("id"))

    if not masa or not siparis_id:
        return jsonify({"ok": False, "msg": "Eksik veri"}), 400

    adisyonlar = load_json(ADISYON_FILE, {})

    if masa not in adisyonlar:
        return jsonify({"ok": False, "msg": "Masa yok"}), 404

    for u in adisyonlar[masa]["urunler"]:
        if u["id"] == siparis_id and not u["hazir"]:
            u["hazir"] = True
            u["hazir_zaman"] = datetime.now().strftime("%H:%M:%S")
            break

    save_json(ADISYON_FILE, adisyonlar)
    return jsonify({"ok": True}), 200


# ================== HAZIR SİPARİŞLER (GARSON) ==================
@app.route("/hazir_siparisler", methods=["GET"])
def hazir_siparisler():
    adisyonlar = load_json(ADISYON_FILE, {})
    menu = load_json(MENU_FILE, {})
    hazirlar = []

    for masa, a in adisyonlar.items():
        for u in a.get("urunler", []):
            if u.get("hazir") and not u.get("bildirildi"):
                menu_id = str(u.get("menu_id"))
                urun_adi = menu.get(menu_id, {}).get("ad", "Ürün")

                hazirlar.append({
                    "masa": masa,
                    "id": u["id"],
                    "urun": urun_adi,
                    "adet": u.get("adet", 1)
                })


    save_json(ADISYON_FILE, adisyonlar)
    return jsonify(hazirlar), 200


@app.route("/hazir_okundu", methods=["POST"])
def hazir_okundu():
    data = request.get_json(force=True)
    siparis_id = (data.get("id"))

    adisyonlar = load_json(ADISYON_FILE, {})

    for masa, a in adisyonlar.items():
        for u in a.get("urunler", []):
            if (u["id"]) == siparis_id:
                u["bildirildi"] = True
                print("OKUNDU:", siparis_id)
                break

    save_json(ADISYON_FILE, adisyonlar)
    return jsonify({"ok": True}), 200

@app.route("/siparis_iptal", methods=["POST"])
def siparis_iptal():
    data = request.get_json(force=True)

    masa = str(data.get("masa", "")).strip()
    menu_id = str(data.get("menu_id"))
    adet = (data.get("adet", 1))
    kullanici = data.get("kullanici", "")

    adisyonlar = load_json(ADISYON_FILE, {})
    menuler = load_json(MENU_FILE, {})

    if masa not in adisyonlar:
        return jsonify({"ok": False, "msg": "Adisyon yok"}), 404

    adisyon = adisyonlar[masa]
    iptal_edilen_id = None

    for u in adisyon["urunler"][:]:
        if str(u["menu_id"]) == menu_id:
            iptal_edilen_id = u["id"]
            if u["adet"] > adet:
                u["adet"] -= adet
            else:
                adisyon["urunler"].remove(u)
            break

    # 🔴 MASA BOŞSA → ADİSYONU TAMAMEN SİL
    if len(adisyon["urunler"]) == 0:
        del adisyonlar[masa]

    save_json(ADISYON_FILE, adisyonlar)

    menu = menuler.get(menu_id, {})
    urun_adi = menu.get("ad", "Ürün")

    iptal_kuyrugu.append({
        "masa": masa,
        "siparis_id": iptal_edilen_id,
        "urun": urun_adi,
        "adet": adet,
        "kullanici": kullanici,
        "zaman": datetime.now().strftime("%H:%M:%S"),
        "onaylandi": False
    })

    return jsonify({"ok": True})


@app.route("/iptaller", methods=["GET"])
def iptaller():
    global iptal_kuyrugu
    data = iptal_kuyrugu[:]
    iptal_kuyrugu.clear()
    return data



# ================== MASA KAPAT ==================
@app.route("/masa_kapat", methods=["POST"])
def masa_kapat():
    data = request.get_json(force=True)

    masa = data.get("masa", "").strip()
    odeme = data.get("odeme", "Nakit")
    kullanici = data.get("kullanici", "Bilinmiyor")

    if not masa:
        return jsonify({"hata": "Masa bilgisi yok"}), 400

    adisyonlar = load_json(ADISYON_FILE, {})
    if masa not in adisyonlar:
        return jsonify({"hata": "Masa bulunamadı"}), 404

    adisyon = adisyonlar[masa]
    if not adisyon.get("urunler"):
        return jsonify({"hata": "Bu masa zaten kapatılmış"}), 400
    menu = load_json(MENU_FILE, {})
    

    toplam = 0
    for u in adisyon.get("urunler", []):
        fiyat = menu.get(str(u["menu_id"]), {}).get("fiyat", 0)
        toplam += int(u["adet"]) * fiyat

    gelirler = load_json(REVENUE_FILE, [])
    gelirler.append({
        "tarih": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "masa": masa,
        "odeme": odeme,
        "tutar": round(toplam, 2),
        "kullanici": kullanici
    })

    save_json(REVENUE_FILE, gelirler)
    satislar = load_json(SATIS_FILE, [])

    urun_listesi = []
    for u in adisyon.get("urunler", []):
        menu_item = menu.get(str(u["menu_id"]), {})
        fiyat = menu_item.get("fiyat", 0)
        adet = int(u["adet"])

        urun_listesi.append({
            "ad": menu_item.get("ad"),
            "adet": adet,
            "tutar": adet * fiyat
        })

    satislar.append({
        "tarih": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "masa": masa,
        "odeme": odeme,
        "kullanici": kullanici,
        "urunler": urun_listesi
    })

    save_json(SATIS_FILE, satislar)
    print("### SATIS YAZILDI:", satislar)
    del adisyonlar[masa]
    save_json(ADISYON_FILE, adisyonlar)

    return jsonify({"ok": True, "toplam": toplam}), 200

@app.route("/masa_tasi", methods=["POST"])
def masa_tasi():
    data = request.get_json(force=True)

    eski = data.get("eski_masa")
    yeni = data.get("yeni_masa")
    kullanici = data.get("kullanici", "Bilinmiyor")

    if not eski or not yeni:
        return jsonify({"ok": False, "msg": "Eksik masa"}), 400

    adisyonlar = load_json(ADISYON_FILE, {})

    if eski not in adisyonlar:
        return jsonify({"ok": False, "msg": "Eski masa yok"}), 404

    if yeni in adisyonlar:
        return jsonify({"ok": False, "msg": "Hedef masa dolu"}), 400

    adisyonlar[yeni] = adisyonlar.pop(eski)
    adisyonlar[yeni]["masa"] = yeni
    adisyonlar[yeni]["tasindi"] = {
        "eskisi": eski,
        "kim": kullanici,
        "zaman": datetime.now().strftime("%H:%M:%S")
    }

    save_json(ADISYON_FILE, adisyonlar)

    return jsonify({"ok": True}), 200

# ================== GELİRLER ==================
@app.route("/gelirler", methods=["GET"])
def gelirleri_getir():
    gelirler = load_json(REVENUE_FILE, [])
    return jsonify(gelirler), 200


# ================== SERVER ==================
print("BASE_DIR =", BASE_DIR)
print("MENU_FILE =", MENU_FILE)
print("MENU EXISTS =", os.path.exists(MENU_FILE))
if __name__ == "__main__":
    print("🚀 Garson Backend Başladı")
    print("SERVER IP:", get_local_ip())
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)





