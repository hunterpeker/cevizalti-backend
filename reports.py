import tkinter as tk
from tkcalendar import DateEntry
from pdf_excel import treeview_pdf_aktar, treeview_excel_aktar
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from data import yukle
import json
import os
import ui_theme
import requests
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOSYA_GIDER = os.path.join(BASE_DIR, "expenses.json")
giderler = yukle(DOSYA_GIDER, [])
FONT_SMALL  = ui_theme.FONT_SMALL
FONT_NORMAL = ui_theme.FONT_NORMAL
FONT_BIG    = ui_theme.FONT_BIG
FONT_TITLE  = ui_theme.FONT_TITLE

import socket

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    finally:
        s.close()

SERVER_URL = "http://192.168.0.50:5000"
print("REPORTS SERVER_URL:", SERVER_URL)


def tarih_araligi_sec(parent):
    frame = ttk.Frame(parent)
    frame.pack(pady=10)

    baslangic = tk.StringVar()
    bitis = tk.StringVar()

    ttk.Label(frame, text="Başlangıç Tarihi").grid(row=0, column=0, padx=5)
    DateEntry(
        frame,
        textvariable=baslangic,
        date_pattern="dd.MM.yyyy",
        width=12
    ).grid(row=0, column=1)

    ttk.Label(frame, text="Bitiş Tarihi").grid(row=0, column=2, padx=5)
    DateEntry(
        frame,
        textvariable=bitis,
        date_pattern="dd.MM.yyyy",
        width=12
    ).grid(row=0, column=3)

    return baslangic, bitis

DOSYA_GELIR = "revenue.json"



# --------------------------------------------------
# YARDIMCI
# --------------------------------------------------
def temizle(parent):
    for w in parent.winfo_children():
        w.destroy()


def json_yukle(dosya, default):
    try:
        with open(dosya, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default


def tarih_parse(t):
    try:
        return datetime.strptime(t[:10], "%d.%m.%Y")
    except:
        return None


# --------------------------------------------------
# ANA RAPOR EKRANI
# --------------------------------------------------
def rapor_ekrani(parent, dosya_gelir, dosya_gider):
    temizle(parent)

    frame = ttk.Frame(parent, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(
        frame,
        text="📊 RAPORLAR",
        font=("Segoe UI", 16, "bold")
    ).pack(pady=10)

    gelirler = json_yukle(dosya_gelir, [])
    giderler = json_yukle(dosya_gider, [])

# --------------------------------------------------
# SATIŞ RAPORU
# --------------------------------------------------
def satis_raporu(parent, dosya_gelir):
    from datetime import datetime, timedelta
    from tkinter import ttk, messagebox
    from pdf_excel import treeview_pdf_aktar, treeview_excel_aktar

    temizle(parent)

    frame = ttk.Frame(parent, padding=20)
    frame.pack(fill="both", expand=True)

    # ================= BAŞLIK =================
    ttk.Label(
        frame,
        text="📈 Satış Raporu",
        font=FONT_TITLE
    ).pack(pady=8)

    gelirler = json_yukle(dosya_gelir, [])

    # ================= TARİH + HESAPLA =================
    ust = ttk.Frame(frame)
    ust.pack(pady=6)

    baslangic = tk.StringVar()
    bitis = tk.StringVar()

    ttk.Label(ust, text="Başlangıç Tarihi").pack(side="left", padx=5)
    DateEntry(
        ust,
        textvariable=baslangic,
        date_pattern="dd.MM.yyyy",
        width=12
    ).pack(side="left")

    ttk.Label(ust, text="Bitiş Tarihi").pack(side="left", padx=5)
    DateEntry(
        ust,
        textvariable=bitis,
        date_pattern="dd.MM.yyyy",
        width=12
    ).pack(side="left")

    # ================= TABLO =================
    tree = ttk.Treeview(
        frame,
        columns=("Tarih", "Masa", "Ödeme", "Tutar", "Kullanıcı"),
        show="headings"
    )

    for c, w in zip(
        ("Tarih", "Masa", "Ödeme", "Tutar", "Kullanıcı"),
        (160, 100, 120, 120, 140)
    ):
        tree.heading(c, text=c)
        tree.column(c, anchor="center", width=w)

    tree.pack(fill="both", expand=True, pady=8)

    # ================= HESAPLA =================
    def hesapla():
        tree.delete(*tree.get_children())

        try:
            b1 = datetime.strptime(baslangic.get(), "%d.%m.%Y")
            b2 = datetime.strptime(bitis.get(), "%d.%m.%Y") + timedelta(days=1)
        except:
            messagebox.showerror("Hata", "Tarih seçiniz")
            return

        toplam = 0.0

        for g in gelirler:
            if g.get("masa") in ("-", "", None):
                continue

            try:
                t = datetime.strptime(g["tarih"], "%d.%m.%Y %H:%M")
            except:
                continue

            if not (b1 <= t < b2):
                continue

            tutar = float(g.get("tutar", 0))
            toplam += tutar

            tree.insert(
                "",
                "end",
                values=(
                    g.get("tarih", ""),
                    g.get("masa", "-"),
                    g.get("odeme", "-"),
                    f"{tutar:.2f} ₺",
                    g.get("kullanici", "")
                )
            )

        lbl_toplam.config(text=f"TOPLAM SATIŞ: {toplam:.2f} ₺")

    # ================= HESAPLA BUTONU (ÜSTTE) =================
    ttk.Button(
        ust,
        text="📊 Hesapla",
        width=14,
        command=hesapla
    ).pack(side="left", padx=12)

    # ================= ALT BAR =================
    alt_bar = ttk.Frame(frame, padding=10)
    alt_bar.pack(fill="x", side="bottom")

    lbl_toplam = ttk.Label(
        alt_bar,
        text="TOPLAM SATIŞ: 0.00 ₺",
        font=FONT_BIG
    )
    lbl_toplam.pack(side="left")

    btns = ttk.Frame(alt_bar)
    btns.pack(side="right")

    ttk.Button(
        btns,
        text="📄 PDF",
        width=12,
        command=lambda: treeview_pdf_aktar("Satış Raporu", [tree])
    ).pack(side="left", padx=5)

    ttk.Button(
        btns,
        text="📊 Excel",
        width=12,
        command=lambda: treeview_excel_aktar("Satış Raporu", [tree])
    ).pack(side="left", padx=5)

    # ================= İLK AÇILIŞ =================
    bugun = datetime.now().strftime("%d.%m.%Y")
    baslangic.set(bugun)
    bitis.set(bugun)
    hesapla()

# STOK RAPORU
# --------------------------------------------------
def stok_raporu(parent, dosya_urun):
    temizle(parent)

    frame = ttk.Frame(parent, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="📦 Stok Raporu",
              font=("Segoe UI", 14, "bold")).pack(pady=10)

    urunler = json_yukle(dosya_urun, {})

    tree = ttk.Treeview(
        frame,
        columns=("Kod", "Ürün", "Stok", "Birim", "Kritik"),
        show="headings",
        height=15
    )

    for c in tree["columns"]:
        tree.heading(c, text=c)
        tree.column(c, anchor="center")

    tree.pack(fill="both", expand=True)

    tree.tag_configure("kritik", background="#ffd6d6")

    for k, u in urunler.items():
        tag = ()
        if u["stok"] <= u.get("kritik", 0):
            tag = ("kritik",)

        tree.insert(
            "",
            "end",
            values=(
                k,
                u["ad"],
                u["stok"],
                u["birim"],
                u.get("kritik", 0)
            ),
            tags=tag
        )


# --------------------------------------------------
# KULLANICI RAPORU
# --------------------------------------------------
def kullanici_raporu(parent, dosya_user):
    temizle(parent)

    frame = ttk.Frame(parent, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(frame, text="👤 Kullanıcı Raporu",
              font=("Segoe UI", 14, "bold")).pack(pady=10)

    users = json_yukle(dosya_user, {})

    tree = ttk.Treeview(
        frame,
        columns=("Kullanıcı", "Rol", "Durum"),
        show="headings",
        height=15
    )

    for c in tree["columns"]:
        tree.heading(c, text=c)
        tree.column(c, anchor="center")

    tree.pack(fill="both", expand=True)

    for u, v in users.items():
        tree.insert(
            "",
            "end",
            values=(
                u,
                v.get("role", ""),
                "Aktif" if v.get("aktif", True) else "Pasif"
            )
        )

# --------------------------------------------------
# SATIN ALMA FİYAT RAPORU
# --------------------------------------------------
def satin_alma_fiyat_raporu(parent, dosya_gider):
    from datetime import datetime, timedelta
    import tkinter as tk
    from tkinter import ttk, messagebox

    temizle(parent)

    frame = ttk.Frame(parent, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(
        frame,
        text="🧾 Satın Alma Fiyat Raporu",
        font=FONT_TITLE
    ).pack(pady=10)

    giderler = json_yukle(dosya_gider, [])

    # ---------- TARİH + HESAPLA ----------
    ust = ttk.Frame(frame)
    ust.pack(pady=5)

    baslangic = tk.StringVar()
    bitis = tk.StringVar()

    ttk.Label(ust, text="Başlangıç").pack(side="left", padx=4)
    DateEntry(ust, textvariable=baslangic,
              date_pattern="dd.MM.yyyy", width=12).pack(side="left")

    ttk.Label(ust, text="Bitiş").pack(side="left", padx=4)
    DateEntry(ust, textvariable=bitis,
              date_pattern="dd.MM.yyyy", width=12).pack(side="left")

    # ---------- ORTA ALAN (TREEVIEW İÇİN) ----------
    center = ttk.Frame(frame)
    center.pack(fill="both", expand=True, pady=10)

    tree = ttk.Treeview(
        center,
        columns=("Tarih", "Ürün", "Miktar", "Birim Fiyat",
                 "Toplam Tutar", "Açıklama", "Kullanıcı"),
        show="headings"
    )

    kolonlar = [
        ("Tarih", 150),
        ("Ürün", 160),
        ("Miktar", 90),
        ("Birim Fiyat", 110),
        ("Toplam Tutar", 120),
        ("Açıklama", 160),
        ("Kullanıcı", 110),
    ]

    for ad, w in kolonlar:
        tree.heading(ad, text=ad)
        tree.column(ad, anchor="center", width=w)

    tree.pack(fill="both", expand=True)

    # ---------- HESAPLA ----------
    def hesapla():
        tree.delete(*tree.get_children())

        try:
            b1 = datetime.strptime(baslangic.get(), "%d.%m.%Y")
            b2 = datetime.strptime(bitis.get(), "%d.%m.%Y") + timedelta(days=1)
        except:
            messagebox.showerror("Hata", "Tarih seçiniz")
            return

        toplam = 0.0

        for g in giderler:
            try:
                t = datetime.strptime(g["tarih"], "%d.%m.%Y %H:%M")
            except:
                continue

            if not (b1 <= t < b2):
                continue

            miktar = float(g.get("miktar", 0))
            tutar = float(g.get("tutar", 0))
            birim = round(tutar / miktar, 2) if miktar else 0
            toplam += tutar

            tree.insert("", "end", values=(
                g.get("tarih", ""),
                g.get("urun", ""),
                f"{miktar:.2f}",
                f"{birim:.2f}",
                f"{tutar:.2f}",
                g.get("aciklama", ""),
                g.get("kullanici", "")
            ))

        lbl_toplam.config(text=f"TOPLAM SATIN ALMA: {toplam:.2f} ₺")

    ttk.Button(ust, text="📊 Hesapla", width=14,
               command=hesapla).pack(side="left", padx=10)

    # ---------- ALT BAR (HER ZAMAN GÖRÜNÜR) ----------
    alt = ttk.Frame(frame, padding=10)
    alt.pack(fill="x", side="bottom")

    lbl_toplam = ttk.Label(
        alt,
        text="TOPLAM SATIN ALMA: 0.00 ₺",
        font=FONT_BIG
    )
    lbl_toplam.pack(side="left")

    ttk.Button(
        alt, text="📊 Excel", width=12,
        command=lambda: treeview_excel_aktar(
            "Satın Alma Fiyat Raporu", [tree])
    ).pack(side="right", padx=5)

    ttk.Button(
        alt, text="📄 PDF", width=12,
        command=lambda: treeview_pdf_aktar(
            "Satın Alma Fiyat Raporu", [tree])
    ).pack(side="right")

    # ---------- İLK AÇILIŞ ----------
    bugun = datetime.now().strftime("%d.%m.%Y")
    baslangic.set(bugun)
    bitis.set(bugun)
    hesapla()


# --------------------------------------------------
# ÜRÜN SATIŞ ADET + TUTAR RAPORU
# (FİLTRELİ + TOPLAM SATIRI TREEVIEW İÇİNDE)
# --------------------------------------------------
def urun_satis_adet_raporu(parent, dosya_satis):
    from datetime import datetime, timedelta
    from tkinter import ttk, messagebox
    import tkinter as tk

    temizle(parent)

    frame = ttk.Frame(parent, padding=20)
    frame.pack(fill="both", expand=True)

    ttk.Label(
        frame,
        text="📦 Ürün Satış Adet Raporu",
        font=FONT_TITLE
    ).pack(pady=10)

    satislar = json_yukle(dosya_satis, [])

    # ================= ÜST BAR =================
    baslangic = tk.StringVar()
    bitis = tk.StringVar()
    urun_filtre = tk.StringVar()

    ust = ttk.Frame(frame)
    ust.pack(fill="x", pady=8)

    # --- SOL (ÜRÜN FİLTRESİ) ---
    ust_sol = ttk.Frame(ust)
    ust_sol.pack(side="left")

    ttk.Label(ust_sol, text="Ürün Filtresi").pack(side="left", padx=5)
    ttk.Entry(
        ust_sol,
        textvariable=urun_filtre,
        width=30
    ).pack(side="left")

    # --- ORTA (TARİHLER) ---
    ust_orta = ttk.Frame(ust)
    ust_orta.pack(side="left", padx=30)

    ttk.Label(ust_orta, text="Başlangıç").pack(side="left", padx=4)
    DateEntry(
        ust_orta,
        textvariable=baslangic,
        date_pattern="dd.MM.yyyy",
        width=12
    ).pack(side="left")

    ttk.Label(ust_orta, text="Bitiş").pack(side="left", padx=4)
    DateEntry(
        ust_orta,
        textvariable=bitis,
        date_pattern="dd.MM.yyyy",
        width=12
    ).pack(side="left")

    # --- SAĞ (HESAPLA) ---
    ust_sag = ttk.Frame(ust)
    ust_sag.pack(side="right")

    ttk.Button(
        ust_sag,
        text="📊 Hesapla",
        width=14,
        command=lambda: hesapla()
    ).pack()

 
    # ================= TABLO =================
    tree = ttk.Treeview(
        frame,
        columns=("urun", "adet", "tutar"),
        show="headings",
        height=15
    )

    tree.heading("urun", text="Ürün")
    tree.heading("adet", text="Satılan Adet")
    tree.heading("tutar", text="Toplam Tutar (₺)")

    tree.column("urun", width=260, anchor="w")
    tree.column("adet", width=120, anchor="center")
    tree.column("tutar", width=160, anchor="e")

    tree.pack(fill="both", expand=True, pady=10)

    tree.tag_configure(
        "toplam",
        background="#f0f0f0",
        font=("Segoe UI", 10, "bold")
    )

    tum_veri = []

    # ================= TABLOYU ÇİZ =================
    def tabloyu_ciz():
        tree.delete(*tree.get_children())

        f = urun_filtre.get().lower().strip()
        toplam_adet = 0
        toplam_tutar = 0.0

        for urun, adet, tutar in tum_veri:
            if f and f not in urun.lower():
                continue

            tree.insert("", "end", values=(urun, adet, f"{tutar:.2f}"))
            toplam_adet += adet
            toplam_tutar += tutar

        tree.insert("", "end", values=("", "", ""))

        tree.insert(
            "", "end",
            values=("TOPLAM", toplam_adet, f"{toplam_tutar:.2f}"),
            tags=("toplam",)
        )

    urun_filtre.trace_add("write", lambda *_: tabloyu_ciz())

    # ================= HESAPLA =================
    def hesapla():
        tum_veri.clear()

        try:
            b1 = datetime.strptime(baslangic.get(), "%d.%m.%Y")
            b2 = datetime.strptime(bitis.get(), "%d.%m.%Y") + timedelta(days=1)
        except:
            messagebox.showerror("Hata", "Tarih seçiniz")
            return

        sayac = {}

        for s in satislar:
            try:
                t = datetime.strptime(s["tarih"], "%d.%m.%Y %H:%M")
            except:
                continue

            if not (b1 <= t < b2):
                continue

            for u in s.get("urunler", []):
                ad = u.get("ad")
                adet = int(u.get("adet", 1))
                tutar = float(u.get("tutar", 0))

                if not ad:
                    continue

                if ad not in sayac:
                    sayac[ad] = [0, 0.0]

                sayac[ad][0] += adet
                sayac[ad][1] += tutar

        for urun, (adet, tutar) in sorted(sayac.items()):
            tum_veri.append((urun, adet, tutar))

        tabloyu_ciz()

    # ================= ALT BAR =================
    alt = ttk.Frame(frame, padding=10)
    alt.pack(fill="x", side="bottom")

    ttk.Button(
        alt, text="📊 Excel", width=12,
        command=lambda: treeview_excel_aktar(
            "Ürün Satış Adet Raporu", [tree])
    ).pack(side="right", padx=5)

    ttk.Button(
        alt, text="📄 PDF", width=12,
        command=lambda: treeview_pdf_aktar(
            "Ürün Satış Adet Raporu", [tree])
    ).pack(side="right")

    # ================= İLK AÇILIŞ =================
    bugun = datetime.now().strftime("%d.%m.%Y")
    baslangic.set(bugun)
    bitis.set(bugun)
    hesapla()

# --------------------------------------------------
# ÖDEME TÜRÜ RAPORU
# --------------------------------------------------
def odeme_raporu(parent):
    import os
    from datetime import datetime, timedelta
    from tkinter import ttk, messagebox
    import tkinter as tk
    from tkcalendar import DateEntry
    from data import yukle

    temizle(parent)

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DOSYA_GELIR = os.path.join(BASE_DIR, "revenue.json")

    frame = ttk.Frame(parent, padding=20)
    frame.pack(fill="both", expand=True)

    # ================= BAŞLIK =================
    ttk.Label(
        frame,
        text="💳 Ödeme Türü Raporu",
        font=FONT_TITLE
    ).pack(pady=8)

    # ================= TARİH + HESAPLA =================
    ust = ttk.Frame(frame)
    ust.pack(pady=6)

    baslangic = tk.StringVar()
    bitis = tk.StringVar()

    ttk.Label(ust, text="Başlangıç Tarihi").pack(side="left", padx=5)
    DateEntry(
        ust,
        textvariable=baslangic,
        date_pattern="dd.MM.yyyy",
        width=12
    ).pack(side="left")

    ttk.Label(ust, text="Bitiş Tarihi").pack(side="left", padx=5)
    DateEntry(
        ust,
        textvariable=bitis,
        date_pattern="dd.MM.yyyy",
        width=12
    ).pack(side="left")

    ttk.Button(
        ust,
        text="📊 Hesapla",
        width=14,
        command=lambda: hesapla()
    ).pack(side="left", padx=12)

    # ================= ORTA ALAN =================
    orta = ttk.Frame(frame)
    orta.pack(fill="both", expand=True, pady=8)

    orta.columnconfigure(0, weight=1)
    orta.columnconfigure(1, weight=1)

    # -------- NAKİT --------
    nakit_frame = ttk.LabelFrame(orta, text="💵 Nakit Ödemeler", padding=10)
    nakit_frame.grid(row=0, column=0, sticky="nsew", padx=6)

    nakit_tree = ttk.Treeview(
        nakit_frame,
        columns=("Tarih", "Masa", "Tutar", "Kullanıcı"),
        show="headings"
    )

    for c, w in zip(("Tarih", "Masa", "Tutar", "Kullanıcı"), (150, 80, 120, 140)):
        nakit_tree.heading(c, text=c)
        nakit_tree.column(c, anchor="center", width=w)

    nakit_tree.pack(fill="both", expand=True)

    # -------- KART --------
    kart_frame = ttk.LabelFrame(orta, text="💳 Kart Ödemeler", padding=10)
    kart_frame.grid(row=0, column=1, sticky="nsew", padx=6)

    kart_tree = ttk.Treeview(
        kart_frame,
        columns=("Tarih", "Masa", "Tutar", "Kullanıcı"),
        show="headings"
    )

    for c, w in zip(("Tarih", "Masa", "Tutar", "Kullanıcı"), (150, 80, 120, 140)):
        kart_tree.heading(c, text=c)
        kart_tree.column(c, anchor="center", width=w)

    kart_tree.pack(fill="both", expand=True)

    # ================= HESAPLA =================
    def hesapla():
        nakit_tree.delete(*nakit_tree.get_children())
        kart_tree.delete(*kart_tree.get_children())

        try:
            b1 = datetime.strptime(baslangic.get(), "%d.%m.%Y")
            b2 = datetime.strptime(bitis.get(), "%d.%m.%Y") + timedelta(days=1)
        except:
            messagebox.showerror("Hata", "Tarih seçiniz")
            return

        gelirler = yukle(DOSYA_GELIR, [])
        nakit_toplam = 0.0
        kart_toplam = 0.0

        for g in gelirler:
            try:
                t = datetime.strptime(g["tarih"], "%d.%m.%Y %H:%M")
            except:
                continue

            if not (b1 <= t < b2):
                continue

            tutar = float(g.get("tutar", 0))

            if g.get("odeme") == "Nakit":
                nakit_toplam += tutar
                nakit_tree.insert(
                    "", "end",
                    values=(g["tarih"], g.get("masa", "-"),
                            f"{tutar:.2f} ₺", g.get("kullanici", "-"))
                )

            elif g.get("odeme") == "Kart":
                kart_toplam += tutar
                kart_tree.insert(
                    "", "end",
                    values=(g["tarih"], g.get("masa", "-"),
                            f"{tutar:.2f} ₺", g.get("kullanici", "-"))
                )

        lbl_nakit.config(text=f"Nakit Toplam: {nakit_toplam:.2f} ₺")
        lbl_kart.config(text=f"Kart Toplam: {kart_toplam:.2f} ₺")

    # ================= ALT BAR =================
    alt_bar = ttk.Frame(frame, padding=10)
    alt_bar.pack(fill="x", side="bottom")

    toplamlar = ttk.Frame(alt_bar)
    toplamlar.pack(side="left")

    lbl_nakit = ttk.Label(toplamlar, text="Nakit Toplam: 0.00 ₺", font=FONT_BIG)
    lbl_nakit.pack(anchor="w")

    lbl_kart = ttk.Label(toplamlar, text="Kart Toplam: 0.00 ₺", font=FONT_BIG)
    lbl_kart.pack(anchor="w")

    btns = ttk.Frame(alt_bar)
    btns.pack(side="right")

    ttk.Button(
        btns,
        text="📊 Excel",
        width=12,
        command=lambda: treeview_excel_aktar(
            "Ödeme Türü Raporu",
            [nakit_tree, kart_tree]
        )
    ).pack(side="left", padx=5)

    ttk.Button(
        btns,
        text="📄 PDF",
        width=12,
        command=lambda: treeview_pdf_aktar(
            "Ödeme Türü Raporu",
            [nakit_tree, kart_tree]
        )
    ).pack(side="left")

    # ================= İLK AÇILIŞ =================
    bugun = datetime.now().strftime("%d.%m.%Y")
    baslangic.set(bugun)
    bitis.set(bugun)
    hesapla()

def kar_zarar_yeni(parent, temizle_cb):
    temizle_cb()

    ana = ttk.Frame(parent, padding=10)
    ana.pack(fill="both", expand=True)

    # ================= ÜST BAR =================
    ust = ttk.Frame(ana)
    ust.pack(fill="x", pady=6)

    baslangic = tk.StringVar()
    bitis = tk.StringVar()

    ttk.Label(ust, text="Başlangıç Tarihi").pack(side="left", padx=4)
    DateEntry(ust, textvariable=baslangic,
              date_pattern="dd.MM.yyyy", width=12).pack(side="left")

    ttk.Label(ust, text="Bitiş Tarihi").pack(side="left", padx=4)
    DateEntry(ust, textvariable=bitis,
              date_pattern="dd.MM.yyyy", width=12).pack(side="left")

    # ================= ORTA ALAN =================
    orta = ttk.Frame(ana)
    orta.pack(fill="both", expand=True, pady=8)

    orta.columnconfigure(0, weight=1, uniform="x")
    orta.columnconfigure(1, weight=1, uniform="x")
    orta.rowconfigure(0, weight=1)

    # ================= GELİRLER =================
    gelir_frame = ttk.LabelFrame(
        orta, text="Gelirler (Satış Detayları)", padding=6
    )
    gelir_frame.grid(row=0, column=0, sticky="nsew", padx=4)

    gelir_tree = ttk.Treeview(
        gelir_frame,
        columns=("Tarih", "Masa", "Ödeme",
                 "Toplam Tutar", "Açıklama", "Kullanıcı"),
        show="headings"
    )
    gelir_tree.pack(fill="both", expand=True)

    gelir_kolonlar = [
        ("Tarih", 135),
        ("Masa", 70),
        ("Ödeme", 80),
        ("Toplam Tutar", 95),
        ("Açıklama", 160),
        ("Kullanıcı", 90),
    ]

    for ad, w in gelir_kolonlar:
        gelir_tree.heading(ad, text=ad)
        gelir_tree.column(ad, width=w, anchor="center")

    # ================= GİDERLER =================
    gider_frame = ttk.LabelFrame(
        orta, text="Giderler (Satın Alma / Harcamalar)", padding=6
    )
    gider_frame.grid(row=0, column=1, sticky="nsew", padx=4)

    gider_tree = ttk.Treeview(
        gider_frame,
        columns=("Tarih", "Kategori", "Ürün",
                 "Miktar", "Birim Fiyat",
                 "Toplam Tutar", "Açıklama", "Kullanıcı"),
        show="headings"
    )
    gider_tree.pack(fill="both", expand=True)

    gider_kolonlar = [
        ("Tarih", 130),
        ("Kategori", 90),
        ("Ürün", 110),
        ("Miktar", 60),
        ("Birim Fiyat", 85),
        ("Toplam Tutar", 95),
        ("Açıklama", 140),
        ("Kullanıcı", 85),
    ]

    for ad, w in gider_kolonlar:
        gider_tree.heading(ad, text=ad)
        gider_tree.column(ad, width=w, anchor="center")

    # ================= ALT BAR =================
    alt = ttk.Frame(ana)
    alt.pack(fill="x", pady=6)

    ozet = ttk.LabelFrame(alt, text="Özet Bilgiler", padding=8)
    ozet.pack(side="left")

    font_lbl = ("Segoe UI", 9)
    font_val = ("Segoe UI", 10, "bold")

    def ozet_satir(row, text):
        ttk.Label(
            ozet, text=text, font=font_lbl
        ).grid(row=row, column=0, sticky="w", padx=(0, 12), pady=2)

        lbl = ttk.Label(
            ozet, text="0.00 ₺", font=font_val
        )
        lbl.grid(row=row, column=1, sticky="e", pady=2)
        return lbl

    lbl_gelir = ozet_satir(0, "Toplam Gelir")
    lbl_gider = ozet_satir(1, "Toplam Gider")
    lbl_net   = ozet_satir(2, "Net Sonuç")
    lbl_nakit = ozet_satir(3, "Nakit Toplam")
    lbl_kart  = ozet_satir(4, "Kart Toplam")

    # ================= EXPORT =================
    from tkinter import filedialog

    def kar_zarar_pdf_aktar():
        dosya = filedialog.asksaveasfilename(
            title="Kar Zarar Raporu",
            defaultextension=".pdf",
            filetypes=[("PDF Dosyası", "*.pdf")]
        )
        if not dosya:
            return

        # 🔥 TEK PDF – GELİR + GİDER
        treeview_pdf_aktar(
            "Kar Zarar Raporu",
            [gelir_tree, gider_tree],
            dosya=dosya
        )


    def kar_zarar_excel_aktar():
        treeview_excel_aktar(
            "Kar Zarar Raporu",
            [gelir_tree, gider_tree]
        )

    sag = ttk.Frame(alt)
    sag.pack(side="right")

    ttk.Button(
        sag,
        text="📄 PDF",
        width=12,
        command=kar_zarar_pdf_aktar
    ).pack(side="left", padx=5)

    ttk.Button(
        sag,
        text="📊 Excel",
        width=12,
        command=kar_zarar_excel_aktar
    ).pack(side="left")


    # ================= HESAPLA =================
    def hesapla():
        global gelirler, giderler
        gelir_tree.delete(*gelir_tree.get_children())
        gider_tree.delete(*gider_tree.get_children())

        try:
            b1 = datetime.strptime(baslangic.get(), "%d.%m.%Y")
            b2 = datetime.strptime(bitis.get(), "%d.%m.%Y") + timedelta(days=1)
        except:
            messagebox.showerror("Hata", "Tarih seçiniz")
            return

        # ---- GELİRLER ----
        try:
            r = requests.get(f"{SERVER_URL}/gelirler", timeout=3)
            gelirler = r.json()
        except Exception as e:
            messagebox.showerror("Hata", f"Gelirler alınamadı:\n{e}")
            return

        giderler = yukle(DOSYA_GIDER, [])

        toplam_gelir = toplam_gider = nakit = kart = 0.0

        for g in gelirler:
            try:
                t = datetime.strptime(g["tarih"][:10], "%d.%m.%Y")
            except:
                continue

            if not (b1 <= t < b2):
                continue

            tutar = float(g.get("tutar", 0))
            toplam_gelir += tutar

            if g.get("odeme") == "Kart":
                kart += tutar
            else:
                nakit += tutar

            gelir_tree.insert("", "end", values=(
                g.get("tarih", ""),
                g.get("masa", "-"),
                g.get("odeme", "-"),
                f"{tutar:.2f}",
                g.get("aciklama", ""),
                g.get("kullanici", "")
            ))

        # ---- GİDERLER (ASİL SORUN BURADAYDI) ----
        for g in giderler:
            try:
                t = datetime.strptime(g["tarih"][:10], "%d.%m.%Y")
            except:
                continue

            if not (b1 <= t < b2):
                continue

            tutar = float(g.get("tutar", 0))
            miktar = float(g.get("miktar", 0))
            bf = round(tutar / miktar, 2) if miktar else 0

            toplam_gider += tutar

            gider_tree.insert("", "end", values=(
                g.get("tarih", ""),
                g.get("kategori", ""),
                g.get("urun", ""),
                f"{miktar:.2f}",
                f"{bf:.2f}",
                f"{tutar:.2f}",
                g.get("aciklama", ""),
                g.get("kullanici", "")
            ))

        lbl_gelir.config(text=f"{toplam_gelir:.2f} ₺")
        lbl_gider.config(text=f"{toplam_gider:.2f} ₺")
        lbl_net.config(text=f"{(toplam_gelir - toplam_gider):.2f} ₺")
        lbl_nakit.config(text=f"{nakit:.2f} ₺")
        lbl_kart.config(text=f"{kart:.2f} ₺")


    ttk.Button(
        ust, text="📊 Hesapla", width=14, command=hesapla
    ).pack(side="left", padx=12)

    # ================= İLK AÇILIŞ =================
    bugun = datetime.now().strftime("%d.%m.%Y")
    baslangic.set(bugun)
    bitis.set(bugun)
    hesapla()
