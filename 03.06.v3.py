# -*- coding: utf-8 -*-
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, date, timedelta
import os
import hashlib
import json
import time
import requests

BOLGELER = ["🏭 Adana LM", "🏭 Tuzla LM"]

MAKINE_LISTESI_BOLGE = {
    "🏭 Adana LM": [
        "VNA-01 (Hat A)", "VNA-02 (Hat A)", "VNA-03 (Hat B)", "VNA-04 (Hat B)",
        "RT-01 (Depo Sahası)", "RT-02 (Depo Sahası)", "RT-03 (Depo Sahası)",
        "Konveyör Hattı 1", "Konveyör Hattı 2", "Konveyör Hattı 3",
        "Kompresör İstasyonu", "Elektrik Panosu MCC-1", "Elektrik Panosu MCC-2",
        "Soğutma Ünitesi", "Jeneratör",
        "Forklift FLT-01", "Forklift FLT-02", "Transpalet-01", "Transpalet-02",
        "Şarj İstasyonu", "Kapı Otomasyonu", "Yangın Sistemi", "Diğer"
    ],
    "🏭 Tuzla LM": [
        "VNA-01 (Tuzla)", "VNA-02 (Tuzla)", "VNA-03 (Tuzla)",
        "RT-01 (Tuzla Depo)", "RT-02 (Tuzla Depo)",
        "Konveyör Hattı 1 (Tuzla)", "Konveyör Hattı 2 (Tuzla)",
        "Kompresör İstasyonu (Tuzla)", "Elektrik Panosu MCC-1 (Tuzla)",
        "Soğutma Ünitesi (Tuzla)", "Jeneratör (Tuzla)",
        "Forklift FLT-01 (Tuzla)", "Forklift FLT-02 (Tuzla)",
        "Transpalet-01 (Tuzla)", "Transpalet-02 (Tuzla)",
        "Şarj İstasyonu (Tuzla)", "Kapı Otomasyonu (Tuzla)",
        "Yangın Sistemi (Tuzla)", "Diğer"
    ]
}

MAKINE_LISTESI = sorted(set(m for bl in MAKINE_LISTESI_BOLGE.values() for m in bl))

ARIZA_TURLERI = {
    "⚡ Elektrik": [
        "Sigorta attı", "Motor arızası", "Sensör hatası", "PLC/Otomasyon hatası",
        "Kablo kopması", "Kontaktör arızası", "Enkoder arızası",
        "Frekans sürücü hatası", "Akü/Şarj sorunu", "Diğer"
    ],
    "⚙️ Mekanik": [
        "Rulman arızası", "Kayış/Zincir kopması", "Dişli hasarı", "Aşınma",
        "Titreşim/Gürültü", "Mil kırılması", "Fren arızası",
        "Lastik/Tekerlek hasarı", "Diğer"
    ],
    "🔧 Tesisat / Hidrolik": [
        "Boru sızıntısı", "Valf arızası", "Pompa sorunu",
        "Basınç düşüklüğü", "Hidrolik yağ kaçağı", "Filtre tıkanması", "Diğer"
    ],
    "🖥️ Elektronik / Yazılım": [
        "HMI ekran hatası", "Ağ/İletişim hatası", "Yazılım/Firmware hatası",
        "Barkod/Okuyucu arızası", "PLC program hatası", "Diğer"
    ],
    "🏗️ Yapısal / İnşaat": [
        "Raf/Kafes yapı hasarı", "Zemin bozulması", "Kapı/Bariyer arızası",
        "Aydınlatma arızası", "Klima/Havalandırma arızası", "Diğer"
    ],
    "🔋 Enerji / Şarj": [
        "Şarj istasyonu arızası", "Akü değişimi gerekli",
        "Güç kaynağı sorunu", "Diğer"
    ],
    "🚒 Güvenlik / Emniyet": [
        "Yangın söndürme sistemi", "Acil durdurma butonu",
        "Güvenlik sensörü", "Bariyer/Işıklı perde arızası", "Diğer"
    ]
}

ARIZA_ONCELIKLERI = {
    "🔴 KRİTİK — Üretim Durdu":   {"renk": "#DC2626", "sla_dk": 30,   "puan": 1},
    "🟠 YÜKSEK — Kısmi Aksama":   {"renk": "#EA580C", "sla_dk": 120,  "puan": 2},
    "🟡 ORTA — Performans Düşük": {"renk": "#D97706", "sla_dk": 480,  "puan": 3},
    "🟢 DÜŞÜK — Planlı Bakım":    {"renk": "#16A34A", "sla_dk": 1440, "puan": 4},
}

KULLANICILAR_DEFAULT = {
    "admin":    {"sifre": hashlib.sha256("1905".encode()).hexdigest(), "rol": "Yönetici",  "tam_ad": "Sistem Yöneticisi"},
    "sezer":    {"sifre": hashlib.sha256("1905".encode()).hexdigest(), "rol": "Yönetici",  "tam_ad": "Sezer Bey"},
    "teknik01": {"sifre": hashlib.sha256("1905".encode()).hexdigest(), "rol": "Teknisyen", "tam_ad": "Teknisyen 1"},
    "uretim":   {"sifre": hashlib.sha256("1905".encode()).hexdigest(), "rol": "Operatör",  "tam_ad": "Üretim Operatörü"},
}

ARIZA_SUTUNLARI = [
    "Talep No", "Bölge", "Durum", "Öncelik", "Vardiya", "Açılış Tarihi", "Kapatma Tarihi",
    "Bildiren", "Bildiren Departman", "Müdahale Eden", "Makine", "Arıza Türü",
    "Alt Kategori", "Arıza Tanımı", "Bildirim Saati", "İlk Müdahale Saati",
    "Çözüm Süresi (Dk)", "SLA Durumu", "Çözüm Açıklaması",
    "Kök Neden", "5 Neden Analizi", "Kaizen Önerisi",
    "Kullanılan Malzemeler", "Malzeme Maliyeti (TL)", "İş Gücü Maliyeti (TL)",
    "Toplam Maliyet (TL)", "Fotoğraf Notu", "Kapatma Onayı"
]

STOK_SUTUNLARI = [
    "Malzeme Kodu", "Malzeme Adı", "Kategori", "Birim",
    "Stok Miktarı", "Kritik Seviye", "Maksimum Stok",
    "Son Fiyat (TL)", "Tedarikçi", "Son Güncelleme"
]

def sb_url():
    try:
        return st.secrets["supabase"]["url"]
    except Exception:
        return ""

def sb_key():
    try:
        return st.secrets["supabase"]["key"]
    except Exception:
        return ""

def sb_headers():
    return {
        "apikey":        sb_key(),
        "Authorization": f"Bearer {sb_key()}",
        "Content-Type":  "application/json",
        "Prefer":        "return=representation"
    }

def secrets_kontrol():
    try:
        u = st.secrets["supabase"]["url"]
        k = st.secrets["supabase"]["key"]
        if not u or not k:
            raise KeyError
        return True
    except (KeyError, FileNotFoundError):
        st.error("⚙️ **Supabase bağlantısı yapılandırılmamış.**")
        st.stop()
        return False

def sb_select(tablo, filtre=""):
    try:
        if not sb_url():
            return []
        url = f"{sb_url()}/rest/v1/{tablo}?{filtre}&order=id.desc" if filtre else f"{sb_url()}/rest/v1/{tablo}?order=id.desc"
        r = requests.get(url, headers=sb_headers(), timeout=10)
        if r.ok:
            result = r.json()
            return result if isinstance(result, list) else []
        return []
    except Exception:
        return []

def sb_insert(tablo, veri):
    try:
        if not sb_url():
            return False
        url = f"{sb_url()}/rest/v1/{tablo}"
        r = requests.post(url, headers=sb_headers(), json=veri, timeout=10)
        return r.ok
    except Exception:
        return False

def sb_update(tablo, filtre, veri):
    try:
        if not sb_url():
            return False
        url = f"{sb_url()}/rest/v1/{tablo}?{filtre}"
        h = sb_headers()
        h["Prefer"] = "return=minimal"
        r = requests.patch(url, headers=h, json=veri, timeout=10)
        return r.ok
    except Exception:
        return False

def sb_delete(tablo, filtre):
    try:
        if not sb_url():
            return False
        url = f"{sb_url()}/rest/v1/{tablo}?{filtre}"
        r = requests.delete(url, headers=sb_headers(), timeout=10)
        return r.ok
    except Exception:
        return False

def sb_to_df(rows, kolon_map=None):
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df = df.drop(columns=[c for c in ["id", "created_at"] if c in df.columns])
    if kolon_map:
        df = df.rename(columns=kolon_map)
    for col in ["Stok Miktarı", "Kritik Seviye", "Maksimum Stok", "Son Fiyat (TL)",
                "Çözüm Süresi (Dk)", "Malzeme Maliyeti (TL)", "İş Gücü Maliyeti (TL)", "Toplam Maliyet (TL)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    for col in df.columns:
        if df[col].dtype == object:
            df[col] = df[col].astype(str)
            df[col] = df[col].replace({"None": "", "nan": "", "none": "", "<NA>": ""})
    return df

ARIZA_KOLON_MAP = {
    "talep_no": "Talep No", "bolge": "Bölge", "durum": "Durum", "oncelik": "Öncelik",
    "vardiya": "Vardiya", "acilis_tarihi": "Açılış Tarihi", "kapatma_tarihi": "Kapatma Tarihi",
    "bildiren": "Bildiren", "bildiren_departman": "Bildiren Departman", "mudahale_eden": "Müdahale Eden",
    "makine": "Makine", "ariza_turu": "Arıza Türü", "alt_kategori": "Alt Kategori",
    "ariza_tanimi": "Arıza Tanımı", "bildirim_saati": "Bildirim Saati",
    "ilk_mudahale_saati": "İlk Müdahale Saati", "cozum_suresi_dk": "Çözüm Süresi (Dk)",
    "sla_durumu": "SLA Durumu", "cozum_aciklamasi": "Çözüm Açıklaması",
    "kok_neden": "Kök Neden", "bes_neden_analizi": "5 Neden Analizi",
    "kaizen_onerisi": "Kaizen Önerisi", "kullanilan_malzemeler": "Kullanılan Malzemeler",
    "malzeme_maliyeti": "Malzeme Maliyeti (TL)", "isguc_maliyeti": "İş Gücü Maliyeti (TL)",
    "toplam_maliyet": "Toplam Maliyet (TL)", "fotograf_notu": "Fotoğraf Notu",
    "kapatma_onayi": "Kapatma Onayı",
}

STOK_KOLON_MAP = {
    "malzeme_kodu": "Malzeme Kodu", "malzeme_adi": "Malzeme Adı", "kategori": "Kategori",
    "birim": "Birim", "stok_miktari": "Stok Miktarı", "kritik_seviye": "Kritik Seviye",
    "maksimum_stok": "Maksimum Stok", "son_fiyat": "Son Fiyat (TL)",
    "tedarikci": "Tedarikçi", "son_guncelleme": "Son Güncelleme",
}

@st.cache_data(ttl=5)
def ariza_df_getir():
    try:
        rows = sb_select("ariza_kayitlari")
        return sb_to_df(rows, ARIZA_KOLON_MAP)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=10)
def stok_df_getir():
    try:
        rows = sb_select("stok")
        return sb_to_df(rows, STOK_KOLON_MAP)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def kullanicilar_getir():
    try:
        rows = sb_select("kullanicilar")
        if not rows:
            return {}
        return {r["kullanici_adi"]: {"sifre": r["sifre_hash"], "rol": r["rol"], "tam_ad": r["tam_ad"]} for r in rows}
    except Exception:
        return {}

def makine_listesi_db():
    try:
        rows = sb_select("makine_listesi", "aktif=eq.true")
        if not rows:
            return {}
        result = {}
        for r in rows:
            result.setdefault(r["bolge"], []).append(r["makine_adi"])
        return result
    except Exception:
        return {}

def ariza_turu_db():
    try:
        url = f"{sb_url()}/rest/v1/ariza_turu_listesi?aktif=eq.true&order=kategori.asc,id.asc"
        r = requests.get(url, headers=sb_headers(), timeout=10)
        if not r.ok:
            return {}
        rows = r.json()
        if not rows:
            return {}
        result = {}
        for row in rows:
            kat = row.get("kategori", "")
            alt = row.get("alt_tur", "")
            if kat and alt:
                result.setdefault(kat, []).append(alt)
        return result
    except Exception:
        return {}

def aktif_makine_listesi():
    db = makine_listesi_db()
    return db if db else MAKINE_LISTESI_BOLGE

def aktif_ariza_turleri():
    db = ariza_turu_db()
    return db if db else ARIZA_TURLERI

def checklist_getir(bakim_plani_id):
    try:
        url = f"{sb_url()}/rest/v1/bakim_checklist?bakim_plani_id=eq.{int(bakim_plani_id)}&aktif=eq.true&order=sira.asc"
        r = requests.get(url, headers=sb_headers(), timeout=10)
        if r.ok:
            rows = r.json()
            return rows if isinstance(rows, list) else []
        return []
    except Exception:
        return []

def checklist_kayit_getir(talep_no):
    try:
        url = f"{sb_url()}/rest/v1/bakim_checklist_kayit?ariza_talep_no=eq.{talep_no}&order=id.asc"
        r = requests.get(url, headers=sb_headers(), timeout=10)
        if r.ok:
            rows = r.json()
            return rows if isinstance(rows, list) else []
        return []
    except Exception:
        return []

def cache_temizle():
    ariza_df_getir.clear()
    stok_df_getir.clear()
    kullanicilar_getir.clear()

@st.cache_data(ttl=3600)
def veritabani_hazirla():
    try:
        u = st.secrets["supabase"]["url"]
        k = st.secrets["supabase"]["key"]
        if not u or not k:
            return
    except Exception:
        return
    if not sb_select("stok"):
        baslangic = [
            {"malzeme_kodu": "M001", "malzeme_adi": "VNA Sürüş Tekerleği (225mm)", "kategori": "Hareketli Parça", "birim": "Adet", "stok_miktari": 8, "kritik_seviye": 2, "maksimum_stok": 15, "son_fiyat": 850, "tedarikci": "Jungheinrich TR", "son_guncelleme": datetime.now().strftime("%d/%m/%Y")},
            {"malzeme_kodu": "M002", "malzeme_adi": "RT Mesafe Sensörü (Sick)", "kategori": "Sensör", "birim": "Adet", "stok_miktari": 12, "kritik_seviye": 3, "maksimum_stok": 20, "son_fiyat": 1200, "tedarikci": "Sick Türkiye", "son_guncelleme": datetime.now().strftime("%d/%m/%Y")},
            {"malzeme_kodu": "M003", "malzeme_adi": "PLC Dijital Giriş Modülü (Siemens)", "kategori": "Elektrik", "birim": "Adet", "stok_miktari": 4, "kritik_seviye": 1, "maksimum_stok": 8, "son_fiyat": 2400, "tedarikci": "Siemens TR", "son_guncelleme": datetime.now().strftime("%d/%m/%Y")},
            {"malzeme_kodu": "M004", "malzeme_adi": "Rulman (6204-2RS)", "kategori": "Mekanik", "birim": "Adet", "stok_miktari": 25, "kritik_seviye": 5, "maksimum_stok": 50, "son_fiyat": 45, "tedarikci": "SKF Türkiye", "son_guncelleme": datetime.now().strftime("%d/%m/%Y")},
            {"malzeme_kodu": "M005", "malzeme_adi": "Hidrolik Yağ ISO-46", "kategori": "Sarf", "birim": "Litre", "stok_miktari": 40, "kritik_seviye": 10, "maksimum_stok": 80, "son_fiyat": 180, "tedarikci": "Shell TR", "son_guncelleme": datetime.now().strftime("%d/%m/%Y")},
            {"malzeme_kodu": "M006", "malzeme_adi": "Konveyör Kayışı (B-1500)", "kategori": "Hareketli Parça", "birim": "Metre", "stok_miktari": 30, "kritik_seviye": 5, "maksimum_stok": 60, "son_fiyat": 95, "tedarikci": "ContiTech", "son_guncelleme": datetime.now().strftime("%d/%m/%Y")},
            {"malzeme_kodu": "M007", "malzeme_adi": "Motor Koruma Sigortası (16A)", "kategori": "Elektrik", "birim": "Adet", "stok_miktari": 20, "kritik_seviye": 5, "maksimum_stok": 40, "son_fiyat": 35, "tedarikci": "ABB TR", "son_guncelleme": datetime.now().strftime("%d/%m/%Y")},
            {"malzeme_kodu": "M008", "malzeme_adi": "Endüstriyel Filtre Elemanı", "kategori": "Sarf", "birim": "Adet", "stok_miktari": 15, "kritik_seviye": 3, "maksimum_stok": 30, "son_fiyat": 220, "tedarikci": "Parker TR", "son_guncelleme": datetime.now().strftime("%d/%m/%Y")},
        ]
        for s in baslangic:
            sb_insert("stok", s)
    if not sb_select("kullanicilar"):
        for k in [
            {"kullanici_adi": "admin",    "sifre_hash": hashlib.sha256("1905".encode()).hexdigest(), "tam_ad": "Sistem Yöneticisi", "rol": "Yönetici"},
            {"kullanici_adi": "sezer",    "sifre_hash": hashlib.sha256("1905".encode()).hexdigest(), "tam_ad": "Sezer Bey", "rol": "Yönetici"},
            {"kullanici_adi": "teknik01", "sifre_hash": hashlib.sha256("1905".encode()).hexdigest(), "tam_ad": "Teknisyen 1", "rol": "Teknisyen"},
            {"kullanici_adi": "uretim",   "sifre_hash": hashlib.sha256("1905".encode()).hexdigest(), "tam_ad": "Üretim Operatörü", "rol": "Operatör"},
        ]:
            sb_insert("kullanicilar", k)

secrets_kontrol()
veritabani_hazirla()

def log_yaz(islem, detay=""):
    sb_insert("sistem_log", {
        "zaman":     datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "kullanici": st.session_state.get("aktif_kullanici", "Sistem"),
        "islem":     islem,
        "detay":     detay
    })

def email_alicilari_getir(kategori):
    """
    kategori: 'kritik_ariza' | 'haftalik_rapor' | 'stok_uyari' | 'talep_kapatma'
    Aktif ve ilgili kategoriye işaretli alıcıların email adreslerini döndürür.
    """
    try:
        rows = sb_select("email_alicilar", f"aktif=eq.true&{kategori}=eq.true")
        return [r["email"].strip() for r in rows if r.get("email")]
    except Exception:
        return []

def email_gonder(konu, icerik, kategori="haftalik_rapor"):
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        gonderici = st.secrets["email"]["gonderici"]
        sifre     = st.secrets["email"]["sifre"]

        alicilar = email_alicilari_getir(kategori)
        if not alicilar:
            # DB'de tanımlı/aktif alıcı yoksa secrets'taki sabit listeye düş (geriye uyumluluk)
            try:
                alici_str = st.secrets["email"]["alici"]
                alicilar  = [a.strip() for a in alici_str.split(",") if a.strip()]
            except Exception:
                alicilar = []

        if not alicilar:
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[TeknikPro CMMS] {konu}"
        msg["From"]    = f"TeknikPro CMMS <{gonderici}>"
        msg["To"]      = ", ".join(alicilar)
        html = f"""<html><body style="font-family:Arial,sans-serif;background:#0f172a;color:#e2e8f0;padding:20px;">
          <div style="max-width:600px;margin:0 auto;background:#1e293b;border-radius:12px;padding:24px;border-left:4px solid #3b82f6;">
            <h2 style="color:#e2e8f0;margin:0 0 16px 0;">{konu}</h2>
            <div style="background:#0f172a;border-radius:8px;padding:16px;font-size:14px;line-height:1.8;color:#cbd5e1;white-space:pre-line;">{icerik}</div>
            <div style="margin-top:20px;font-size:11px;color:#475569;border-top:1px solid #334155;padding-top:12px;">{datetime.now().strftime("%d/%m/%Y %H:%M")} — Adana LM / Tuzla LM</div>
          </div></body></html>"""
        msg.attach(MIMEText(html, "html", "utf-8"))
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gonderici, sifre)
            server.sendmail(gonderici, alicilar, msg.as_string())
        return True
    except KeyError:
        return False
    except Exception as e:
        print(f"Email gönderilemedi: {e}")
        return False

def haftalik_rapor_gonder():
    """
    Haftalık bakım raporu gönderimi.

    ÖNEMLİ — RACE CONDITION DÜZELTMESİ:
    Streamlit her kullanıcı etkileşiminde / rerun'da bu fonksiyonu modül seviyesinde
    tekrar çağırır. Eski mantıkta önce "gönderildi mi" kontrolü yapılıp, sonra mail
    gönderilip, sonra kayıt yazılıyordu. Bu üç adım arasındaki zaman boşluğunda
    aynı anda gelen birden fazla rerun, hepsi "henüz gönderilmemiş" görüp mail
    gönderebiliyordu.

    Yeni mantık: önce bir "kilit" satırı insert edilmeye çalışılır. Veritabanındaki
    haftalik_rapor_log.hafta kolonu üzerinde UNIQUE constraint olduğu için, aynı
    hafta_no için ikinci insert veritabanı seviyesinde reddedilir (kilit_ok=False)
    ve fonksiyon hemen çıkar. Sadece kilidi başarıyla alan tek instance mail
    gönderip durumu günceller. Bu, check-then-act yarışını ortadan kaldırır.

    Gerekli SQL (bir kez çalıştırılmalı):
        ALTER TABLE haftalik_rapor_log ADD CONSTRAINT hafta_unique UNIQUE (hafta);
    """
    try:
        bugun = date.today()
        if bugun.weekday() != 0:
            return
        hafta_no = bugun.strftime("%Y-W%W")

        # ÖNCE kilit satırını yazmayı dene. Unique constraint sayesinde aynı hafta
        # için ikinci insert başarısız olur -> mail tekrar gitmez.
        kilit_ok = sb_insert("haftalik_rapor_log", {
            "gonderim_tarihi": datetime.now().strftime("%d/%m/%Y %H:%M"),
            "hafta": hafta_no,
            "durum": "Gönderiliyor"
        })
        if not kilit_ok:
            return  # Bu hafta için kilit zaten alınmış (başka rerun veya zaten gönderilmiş)

        df_h = ariza_df_getir()
        if df_h.empty:
            sb_update("haftalik_rapor_log", f"hafta=eq.{hafta_no}", {"durum": "Hata-BosVeri"})
            return

        gecen_pzt = bugun - timedelta(days=7)
        gecen_paz = bugun - timedelta(days=1)
        try:
            df_h["_t"] = pd.to_datetime(df_h["Açılış Tarihi"], format="%d/%m/%Y %H:%M", errors="coerce").dt.date
            df_hafta = df_h[(df_h["_t"] >= gecen_pzt) & (df_h["_t"] <= gecen_paz)]
        except:
            df_hafta = df_h
        toplam_h   = len(df_hafta)
        acik_h     = len(df_h[df_h["Durum"] == "Açık"])
        kritik_h   = len(df_h[(df_h["Durum"] == "Açık") & (df_h["Öncelik"].str.startswith("🔴", na=False))])
        kapali_h   = len(df_hafta[df_hafta["Durum"] == "Kapalı"])
        sla_asan_h = len(df_hafta[df_hafta["SLA Durumu"].str.contains("Aşıldı", na=False)])
        sla_oran_h = round((toplam_h - sla_asan_h) / max(toplam_h, 1) * 100, 1)
        df_kap_h = df_hafta[df_hafta["Durum"] == "Kapalı"].copy()
        df_kap_h["sure"] = pd.to_numeric(df_kap_h.get("Çözüm Süresi (Dk)", pd.Series(dtype=float)), errors="coerce").fillna(0)
        ort_mttr_h   = round(df_kap_h["sure"].mean(), 1) if not df_kap_h.empty else 0
        toplam_mal_h = pd.to_numeric(df_hafta.get("Toplam Maliyet (TL)", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()
        en_sorunlu = df_hafta["Makine"].value_counts().head(3).to_dict() if not df_hafta.empty and "Makine" in df_hafta.columns else {}
        en_sorunlu_txt = "\n".join([f"  • {k}: {v} arıza" for k, v in en_sorunlu.items()]) or "  • Veri yok"
        kritik_listesi = df_h[(df_h["Durum"] == "Açık") & (df_h["Öncelik"].str.startswith("🔴", na=False))].head(5)
        kritik_txt = ""
        for _, r in kritik_listesi.iterrows():
            kritik_txt += f"  • [{r.get('Talep No', '')}] {r.get('Makine', '')} — {str(r.get('Arıza Tanımı', ''))[:50]}\n"
        kritik_txt = kritik_txt or "  • Kritik açık talep yok ✅"
        icerik = f"""Geçen haftanın ({gecen_pzt.strftime('%d/%m/%Y')} - {gecen_paz.strftime('%d/%m/%Y')}) bakım ve arıza özeti:\n\nBu Hafta Açılan: {toplam_h} | Kapatılan: {kapali_h} | SLA Uyum: %{sla_oran_h} | MTTR: {ort_mttr_h} dk\n\nKritik Açık:\n{kritik_txt}\n\nEn Sorunlu Makineler:\n{en_sorunlu_txt}"""
        konu = f"📊 Haftalık Bakım Raporu — {gecen_pzt.strftime('%d/%m')} - {gecen_paz.strftime('%d/%m/%Y')}"

        basari = email_gonder(konu, icerik, kategori="haftalik_rapor")
        sb_update("haftalik_rapor_log", f"hafta=eq.{hafta_no}", {
            "durum": "Gönderildi" if basari else "Hata"
        })
    except Exception as e:
        print(f"Haftalık rapor hatası: {e}")

try:
    haftalik_rapor_gonder()
except Exception:
    pass

def sla_hesapla(oncelik, acilis, kapanis=None):
    sla_dk = ARIZA_ONCELIKLERI.get(oncelik, {}).get("sla_dk", 480)
    try:
        ac    = datetime.strptime(acilis, "%d/%m/%Y %H:%M")
        bitis = datetime.strptime(kapanis, "%d/%m/%Y %H:%M") if kapanis else datetime.now()
        gecen = (bitis - ac).total_seconds() / 60
        return {"gecen_dk": int(gecen), "sla_dk": sla_dk, "oran": round(gecen / sla_dk * 100, 1),
                "durum": "✅ SLA İçinde" if gecen <= sla_dk else "⚠️ SLA Aşıldı"}
    except:
        return {"gecen_dk": 0, "sla_dk": sla_dk, "oran": 0, "durum": "—"}

def talep_no_uret():
    yil = datetime.now().year
    ay  = datetime.now().month
    prefix = f"ARZ-{yil}{ay:02d}-"
    rows = sb_select("ariza_kayitlari", f"talep_no=like.{prefix}*")
    return f"{prefix}{len(rows)+1:03d}"

def sifre_hashle(sifre):
    return hashlib.sha256(sifre.encode()).hexdigest()

def kullanicilari_yukle():
    try:
        k = kullanicilar_getir()
        return k if k else KULLANICILAR_DEFAULT
    except:
        return KULLANICILAR_DEFAULT

# =============================================================================
# SAYFA KONFİGÜRASYONU & CSS
# =============================================================================

st.set_page_config(page_title="TeknikPro CMMS v2.0", page_icon="🛡️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; font-size: 14px; }
.stApp { background: linear-gradient(160deg, #2D0052 0%, #3D0066 50%, #2D0052 100%) !important; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #1E0038 0%, #2D0052 100%) !important; border-right: 2px solid rgba(255,215,0,0.2) !important; }
[data-testid="stSidebar"] * { color: #E8D5FF !important; }
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 { color: #FFD700 !important; }
[data-testid="metric-container"] { background: rgba(61,0,102,0.8) !important; border: 1px solid rgba(255,215,0,0.25) !important; border-radius: 12px !important; padding: 16px 20px !important; }
[data-testid="metric-container"] label { color: #C89EE8 !important; font-size: 12px !important; font-weight: 600 !important; text-transform: uppercase; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #FFD700 !important; font-size: 28px !important; font-weight: 800 !important; }
h1 { color: #FFD700 !important; font-weight: 800 !important; font-size: 26px !important; }
h2 { color: #FFD700 !important; font-weight: 700 !important; }
h3 { color: #E8D5FF !important; font-weight: 600 !important; }
h4 { color: #C89EE8 !important; font-weight: 600 !important; }
strong { color: #FFD700 !important; }
em { color: #C89EE8 !important; }
li { color: #E8D5FF !important; }
td, th { color: #E8D5FF !important; }
th { color: #FFD700 !important; font-weight: 700 !important; }
p, span, li { color: #E8D5FF !important; }
label { color: #C89EE8 !important; font-size: 13px !important; }
[data-testid="stTabs"] [role="tablist"] { background: rgba(30,0,56,0.8) !important; border-radius: 10px !important; padding: 4px !important; border: 1px solid rgba(255,215,0,0.2) !important; }
[data-testid="stTabs"] [role="tab"] { color: #9B6FBF !important; font-weight: 500 !important; font-size: 13px !important; border-radius: 8px !important; padding: 8px 16px !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { background: rgba(255,215,0,0.15) !important; color: #FFD700 !important; border: 1px solid rgba(255,215,0,0.4) !important; font-weight: 700 !important; }
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea { background: rgba(30,0,56,0.9) !important; border: 1px solid rgba(255,215,0,0.25) !important; border-radius: 8px !important; color: #F5F0FF !important; }
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus { border-color: rgba(255,215,0,0.6) !important; box-shadow: 0 0 0 3px rgba(255,215,0,0.1) !important; }
[data-baseweb="popover"],[data-baseweb="popover"] * { background-color: #2D0052 !important; color: #F5F0FF !important; }
ul[role="listbox"] { background-color: #2D0052 !important; border: 1px solid rgba(255,215,0,0.3) !important; border-radius: 8px !important; }
li[role="option"] { background-color: #2D0052 !important; color: #E8D5FF !important; }
li[role="option"]:hover,li[role="option"][aria-selected="true"] { background-color: #4A0080 !important; color: #FFD700 !important; }
.stButton > button { background: linear-gradient(135deg, #5C0099, #7B00CC) !important; color: #FFD700 !important; border: 1px solid rgba(255,215,0,0.3) !important; border-radius: 8px !important; font-weight: 700 !important; transition: all 0.2s !important; }
.stButton > button:hover { background: linear-gradient(135deg, #FFD700, #FFC200) !important; color: #2D0052 !important; border-color: #FFD700 !important; transform: translateY(-1px) !important; box-shadow: 0 4px 16px rgba(255,215,0,0.3) !important; }
[data-testid="stFormSubmitButton"] > button { background: linear-gradient(135deg, #FFD700, #FFC200) !important; color: #2D0052 !important; border: none !important; width: 100% !important; font-weight: 800 !important; border-radius: 10px !important; font-size: 15px !important; }
[data-testid="stFormSubmitButton"] > button:hover { background: linear-gradient(135deg, #E91E8C, #C2185B) !important; color: #ffffff !important; box-shadow: 0 4px 16px rgba(233,30,140,0.4) !important; }
[data-testid="stDownloadButton"] > button { background: rgba(61,0,102,0.8) !important; border: 1px solid rgba(255,215,0,0.3) !important; color: #FFD700 !important; border-radius: 8px !important; }
[data-testid="stDataFrame"] { border: 1px solid rgba(255,215,0,0.15) !important; border-radius: 12px !important; }
[data-testid="stAlert"] { border-radius: 10px !important; border-left-width: 4px !important; }
[data-testid="stExpander"] { background: rgba(61,0,102,0.5) !important; border: 1px solid rgba(255,215,0,0.15) !important; border-radius: 10px !important; }
[data-testid="stExpander"] summary { color: #FFD700 !important; font-weight: 600 !important; }
[data-testid="stNumberInput"] input { background: rgba(30,0,56,0.9) !important; border: 1px solid rgba(255,215,0,0.25) !important; border-radius: 8px !important; color: #F5F0FF !important; }
hr { border-color: rgba(255,215,0,0.15) !important; }
.durum-karti { background: rgba(61,0,102,0.7); border: 1px solid rgba(255,215,0,0.2); border-radius: 12px; padding: 16px 20px; margin-bottom: 12px; }
.kritik-banner { background: linear-gradient(135deg, rgba(233,30,140,0.15), rgba(180,0,100,0.1)); border: 1px solid rgba(233,30,140,0.5); border-left: 4px solid #E91E8C; border-radius: 10px; padding: 14px 18px; margin: 8px 0 16px 0; }
.sla-badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; }
.sla-ok   { background: rgba(255,215,0,0.15); border:1px solid rgba(255,215,0,0.4); color:#FFD700; }
.sla-warn { background: rgba(233,30,140,0.15); border:1px solid rgba(233,30,140,0.4); color:#E91E8C; }
[data-testid="stProgress"] > div > div { background: #FFD700 !important; }
[data-testid="stRadio"] label { color: #E8D5FF !important; }

/* ── STREAMLIT TOOLBAR GİZLE ───────────────────────────────── */
header[data-testid="stHeader"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }

/* ── MOBİL OPTİMİZASYON ────────────────────────────────────── */
@media (max-width: 768px) {
    .main .block-container { padding: 8px 12px !important; }
    p, span, div, li { color: #F0E8FF !important; font-size: 14px !important; }
    label { color: #FFD700 !important; font-size: 13px !important; font-weight: 600 !important; margin-bottom: 4px !important; }
    [data-testid="stTextInput"] > div { background: rgba(30,0,56,0.95) !important; border: 2px solid rgba(255,215,0,0.5) !important; border-radius: 10px !important; }
    [data-testid="stTextInput"] input { background: transparent !important; border: none !important; box-shadow: none !important; min-height: 44px !important; font-size: 16px !important; color: #FFFFFF !important; padding: 10px 12px !important; }
    [data-testid="stTextArea"] > div { background: rgba(30,0,56,0.95) !important; border: 2px solid rgba(255,215,0,0.5) !important; border-radius: 10px !important; }
    [data-testid="stTextArea"] textarea { background: transparent !important; border: none !important; box-shadow: none !important; font-size: 15px !important; color: #FFFFFF !important; padding: 10px 12px !important; }
    [data-testid="stSelectbox"] > div > div { background: rgba(30,0,56,0.95) !important; border: 2px solid rgba(255,215,0,0.5) !important; border-radius: 10px !important; min-height: 44px !important; }
    [data-testid="stSelectbox"] > div > div > div { background: transparent !important; border: none !important; box-shadow: none !important; }
    [data-testid="stSelectbox"] span, [data-testid="stSelectbox"] p { color: #FFFFFF !important; font-size: 15px !important; }
    [data-testid="stNumberInput"] > div { background: rgba(30,0,56,0.95) !important; border: 2px solid rgba(255,215,0,0.5) !important; border-radius: 10px !important; }
    [data-testid="stNumberInput"] input { background: transparent !important; border: none !important; box-shadow: none !important; min-height: 44px !important; font-size: 16px !important; color: #FFFFFF !important; }
    [data-testid="stTimeInput"] > div { background: rgba(30,0,56,0.95) !important; border: 2px solid rgba(255,215,0,0.5) !important; border-radius: 10px !important; }
    [data-testid="stTimeInput"] input { background: transparent !important; border: none !important; box-shadow: none !important; min-height: 44px !important; font-size: 16px !important; color: #FFFFFF !important; }
    .stButton > button { min-height: 48px !important; font-size: 15px !important; padding: 12px 16px !important; }
    [data-testid="stFormSubmitButton"] > button { min-height: 52px !important; font-size: 16px !important; font-weight: 800 !important; padding: 14px !important; }
    h1 { color: #FFD700 !important; font-size: 18px !important; margin-bottom: 4px !important; }
    h2 { color: #FFD700 !important; font-size: 16px !important; }
    h3 { color: #F0E8FF !important; font-size: 15px !important; }
    h4 { color: #F0E8FF !important; font-size: 14px !important; }
    strong { color: #FFD700 !important; }
    [data-testid="stVerticalBlock"] > div { gap: 6px !important; }
    [data-testid="stTabs"] [role="tab"] { font-size: 10px !important; padding: 5px 8px !important; color: #C89EE8 !important; }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] { color: #FFD700 !important; font-weight: 700 !important; }
    [data-testid="metric-container"] { padding: 10px 12px !important; }
    [data-testid="metric-container"] label { color: #C89EE8 !important; font-size: 11px !important; }
    [data-testid="metric-container"] [data-testid="stMetricValue"] { font-size: 22px !important; color: #FFD700 !important; }
    [data-testid="stCaptionContainer"] p { font-size: 11px !important; color: #9B6FBF !important; }
    [data-testid="stAlert"] p { color: #FFFFFF !important; font-size: 14px !important; }
}
</style>
""", unsafe_allow_html=True)

# =============================================================================
# YETKİLENDİRME
# =============================================================================

def sidebar_giris():
    with st.sidebar:
        st.markdown("---")
        kullanicilar = kullanicilari_yukle()
        if not st.session_state.get("oturum_acik", False):
            try:
                df_durum = ariza_df_getir()
                if not df_durum.empty and "Durum" in df_durum.columns:
                    _k = len(df_durum[(df_durum["Durum"]=="Açık") & (df_durum["Öncelik"].str.startswith("🔴",na=False))])
                    _a = len(df_durum[df_durum["Durum"]=="Açık"])
                else:
                    _k, _a = 0, 0
            except:
                _k, _a = 0, 0

            if _k >= 3:
                emoji, baslik, mesaj, renk = "🚨", "Yoğun Gün", f"{_k} kritik arıza aktif — ekip tam gaz çalışıyor", "#E91E8C"
            elif _k > 0:
                emoji, baslik, mesaj, renk = "⚡", "Dikkat Gerekli", f"{_k} kritik arıza müdahale bekliyor", "#FFD700"
            elif _a >= 8:
                emoji, baslik, mesaj, renk = "📋", "Yoğun Trafik", f"{_a} açık talep var, sistem çalışıyor", "#C89EE8"
            elif _a > 0:
                emoji, baslik, mesaj, renk = "🛠️", "Her Şey Kontrol Altında", f"{_a} açık talep takipte", "#9B6FBF"
            else:
                emoji, baslik, mesaj, renk = "✅", "Tertemiz!", "Açık arıza yok, tesis sakin", "#4ade80"

            st.markdown(f"""
            <div style="background:rgba(61,0,102,0.6);border:1px solid {renk}44;border-radius:10px;padding:16px;text-align:center;">
              <div style="font-size:28px;margin-bottom:6px;">{emoji}</div>
              <div style="font-size:13px;font-weight:700;color:{renk};margin-bottom:4px;">{baslik}</div>
              <div style="font-size:11px;color:#9B6FBF;line-height:1.4;">{mesaj}</div>
            </div>""", unsafe_allow_html=True)
        else:
            tam_ad = st.session_state.aktif_tam_ad
            rol    = st.session_state.aktif_rol
            st.markdown(f"""
            <div style="background:rgba(30,58,138,0.2);border:1px solid rgba(99,179,237,0.25);border-radius:10px;padding:14px 16px;margin-bottom:8px;">
              <div style="font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;">AKTİF OTURUM</div>
              <div style="font-size:15px;color:#e2e8f0;font-weight:600;">👤 {tam_ad}</div>
              <div style="font-size:12px;color:#93c5fd;margin-top:4px;">🏷️ {rol}</div>
            </div>""", unsafe_allow_html=True)
            components.html("""
            <div id="os" style="font-size:11px;color:#475569;padding:0 4px;margin-bottom:6px;">--</div>
            <script>
            function tick(){var n=new Date(),g=["Oca","Şub","Mar","Nis","May","Haz","Tem","Ağu","Eyl","Eki","Kas","Ara"];
            var e=document.getElementById("os");
            if(e)e.textContent=String(n.getDate()).padStart(2,"0")+" "+g[n.getMonth()]+" "+n.getFullYear()+"  "+String(n.getHours()).padStart(2,"0")+":"+String(n.getMinutes()).padStart(2,"0")+":"+String(n.getSeconds()).padStart(2,"0");}
            tick();setInterval(tick,1000);</script>""", height=24)
            if st.button("🚪 Çıkış Yap", use_container_width=True):
                log_yaz("ÇIKIŞ", f"{tam_ad} sistemden çıktı")
                for k in ["oturum_acik", "aktif_kullanici", "aktif_tam_ad", "aktif_rol"]:
                    st.session_state.pop(k, None)
                st.rerun()

def yetkili_mi(min_rol="Operatör"):
    ROL = {"Yönetici": 3, "Teknisyen": 2, "Operatör": 1}
    return ROL.get(st.session_state.get("aktif_rol", ""), 0) >= ROL.get(min_rol, 99)

def giris_gerektir(min_rol="Teknisyen"):
    if not st.session_state.get("oturum_acik", False):
        st.markdown("""<div style="text-align:center;padding:60px 20px;">
          <div style="font-size:48px;">🔒</div>
          <div style="font-size:18px;color:#94a3b8;font-weight:600;">Bu bölüme erişmek için giriş yapın</div>
        </div>""", unsafe_allow_html=True)
        return False
    if not yetkili_mi(min_rol):
        st.error(f"⛔ Bu işlem için **{min_rol}** yetkisi gereklidir.")
        return False
    return True

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("""
    <div style="padding:20px 8px 8px;">
      <div style="font-size:10px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:#3b82f6;margin-bottom:4px;">ENTERPRISE CMMS</div>
      <div style="font-size:20px;font-weight:800;color:#e2e8f0;line-height:1.2;">TeknikPro<br><span style="color:#FFD700;">v2.0</span></div>
      <div style="font-size:11px;color:#475569;margin-top:6px;">TPM & Arıza Yönetim Platformu</div>
    </div>""", unsafe_allow_html=True)

    try:
        df_sb = ariza_df_getir()
        if not df_sb.empty and "Durum" in df_sb.columns:
            _acik   = len(df_sb[df_sb["Durum"] == "Açık"])
            _kritik = len(df_sb[(df_sb["Durum"] == "Açık") & (df_sb["Öncelik"].str.startswith("🔴", na=False))])
        else:
            _acik, _kritik = 0, 0
        st.markdown(f"""
        <div style="display:flex;gap:8px;margin:16px 8px 8px;">
          <div style="flex:1;background:rgba(220,38,38,0.1);border:1px solid rgba(220,38,38,0.3);border-radius:8px;padding:10px 12px;text-align:center;">
            <div style="font-size:22px;font-weight:700;color:#f87171;">{_kritik}</div>
            <div style="font-size:10px;color:#94a3b8;font-weight:600;margin-top:2px;">KRİTİK</div>
          </div>
          <div style="flex:1;background:rgba(234,88,12,0.1);border:1px solid rgba(234,88,12,0.3);border-radius:8px;padding:10px 12px;text-align:center;">
            <div style="font-size:22px;font-weight:700;color:#fb923c;">{_acik}</div>
            <div style="font-size:10px;color:#94a3b8;font-weight:600;margin-top:2px;">AÇIK</div>
          </div>
        </div>""", unsafe_allow_html=True)
    except:
        pass

    st.markdown("---")
    st.markdown("<div style='font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#475569;padding-left:4px;margin-bottom:8px;'>HIZLI BİLGİ</div>", unsafe_allow_html=True)
    st.markdown(f"""<div style="font-size:12px;color:#64748b;padding-left:4px;line-height:1.8;">
      📅 {datetime.now().strftime("%A, %d %B %Y")}<br>
      🏭 Tesis: Adana LM / Tuzla LM<br>📋 Sistem: CMMS v2.0</div>""", unsafe_allow_html=True)
    components.html("""
    <div style="font-size:12px;color:#64748b;padding-left:4px;margin-top:-6px;">
      🕐 <span id="saat" style="color:#64748b;">--:--:--</span> (Türkiye)</div>
    <script>
    function tick(){var n=new Date(),e=document.getElementById("saat");
    if(e)e.textContent=String(n.getHours()).padStart(2,"0")+":"+String(n.getMinutes()).padStart(2,"0")+":"+String(n.getSeconds()).padStart(2,"0");}
    tick();setInterval(tick,1000);</script>""", height=28)

sidebar_giris()

with st.sidebar:
    st.markdown("---")
    st.markdown("""<div style='font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#3b82f6;padding-left:4px;margin-bottom:8px;'>📱 HIZLI ARIZA BİLDİRİM</div>""", unsafe_allow_html=True)
    qr_kod_giris = st.text_input("Makine Kodu", placeholder="Örn: VNA1", help="Makine üzerindeki kodu yazın — Enter'a basın", key="sidebar_qr_kod", label_visibility="collapsed").strip().upper()
    st.caption("👆 Makine kodunu yazıp Enter'a basın")
    if qr_kod_giris:
        try:
            qr_rows = sb_select("qr_kodlar", f"kod=eq.{qr_kod_giris}&aktif=eq.true")
            if qr_rows:
                st.session_state["qr_makine"] = qr_rows[0]["makine"]
                st.session_state["qr_bolge"]  = qr_rows[0]["bolge"]
                st.session_state["goto_yeni_talep"] = True
                st.success(f"✅ {qr_rows[0]['makine']}\n{qr_rows[0]['bolge']}")
            else:
                st.error("❌ Kod bulunamadı")
        except:
            pass

st.markdown("""
<div style="margin-bottom:24px;">
  <h1 style="margin:0;padding:0;">🛡️ Teknik Bakım & Arıza Yönetim Sistemi</h1>
  <p style="color:#475569;font-size:13px;margin-top:4px;">Computerized Maintenance Management System — Endüstriyel TPM Platformu</p>
</div>""", unsafe_allow_html=True)

_goto_yeni = st.session_state.get("goto_yeni_talep", False)
if _goto_yeni:
    st.session_state["goto_yeni_talep"] = False
    components.html("""
    <script>
    function clickYeniTalep() {
        var tabs = window.parent.document.querySelectorAll('[role="tab"]');
        for (var i = 0; i < tabs.length; i++) {
            if (tabs[i].innerText.indexOf("Yeni Talep") >= 0) { tabs[i].click(); return; }
        }
    }
    setTimeout(clickYeniTalep, 300);
    setTimeout(clickYeniTalep, 800);
    setTimeout(clickYeniTalep, 1500);
    </script>""", height=0)

tab_pano, tab_yeni, tab_kapat, tab_rapor, tab_stok, tab_bakim, tab_oee, tab_ai, tab_twin, tab_ayar = st.tabs([
    "📊 Canlı Pano", "➕ Yeni Talep Aç", "✅ Talep Kapat",
    "📋 Raporlama & Arşiv", "📦 Stok Yönetimi", "🔧 Bakım Planları",
    "📈 OEE Analizi", "🤖 AI Tahmin", "🏭 Dijital İkiz", "⚙️ Sistem Ayarları"
])

# =============================================================================
# SEKME 1: CANLI PANO
# =============================================================================

with tab_pano:
    if not st.session_state.get("oturum_acik", False):
        # ── ANA SAYFA GİRİŞ FORMU (MOBİL UYUMLU) ──
        st.markdown("""
        <div style="text-align:center;padding:40px 20px 20px;">
          <div style="font-size:64px;margin-bottom:12px;">🛡️</div>
          <div style="font-size:24px;font-weight:800;color:#FFD700;margin-bottom:4px;">TeknikPro CMMS v2.0</div>
          <div style="font-size:14px;color:#C89EE8;margin-bottom:24px;">Enterprise Bakım & Arıza Yönetim Sistemi<br>Adana LM & Tuzla LM</div>
        </div>""", unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            kullanicilar_login = kullanicilari_yukle()
            with st.form("ana_giris_formu", clear_on_submit=True):
                st.markdown("<div style='text-align:center;font-size:20px;font-weight:700;color:#FFD700;margin-bottom:16px;'>🔐 Sistem Girişi</div>", unsafe_allow_html=True)
                k_input = st.text_input("Kullanıcı Adı", placeholder="kullanici_adi")
                s_input = st.text_input("Şifre", type="password", placeholder="••••••")
                giris_btn = st.form_submit_button("Giriş Yap →", use_container_width=True)
                if giris_btn:
                    k_input = k_input.strip().lower()
                    if k_input in kullanicilar_login and kullanicilar_login[k_input]["sifre"] == sifre_hashle(s_input):
                        st.session_state.oturum_acik     = True
                        st.session_state.aktif_kullanici = k_input
                        st.session_state.aktif_tam_ad    = kullanicilar_login[k_input]["tam_ad"]
                        st.session_state.aktif_rol       = kullanicilar_login[k_input]["rol"]
                        log_yaz("GİRİŞ", f"{kullanicilar_login[k_input]['tam_ad']} sisteme giriş yaptı")
                        st.rerun()
                    else:
                        st.error("❌ Hatalı kullanıcı adı veya şifre.")
    else:
        col_ref, _ = st.columns([1, 8])
        with col_ref:
            if st.button("🔄 Yenile", use_container_width=True):
                ariza_df_getir.clear()
                st.rerun()

        df = ariza_df_getir()

        if df.empty or "Durum" not in df.columns:
            st.info("📭 Sistemde henüz kayıt bulunmuyor.")
        else:
            toplam   = len(df)
            acik     = len(df[df["Durum"] == "Açık"])
            kapali   = len(df[df["Durum"] == "Kapalı"])
            kritik   = len(df[(df["Durum"] == "Açık") & (df["Öncelik"].str.startswith("🔴", na=False))])
            sla_asan = len(df[df["SLA Durumu"].str.contains("Aşıldı", na=False)])
            bugun    = datetime.now().strftime("%d/%m/%Y")
            bugun_s  = len(df[df["Açılış Tarihi"].str.startswith(bugun, na=False)]) if "Açılış Tarihi" in df.columns else 0
            sla_basari = round((toplam - sla_asan) / max(toplam, 1) * 100, 1)

            df_kap = df[df["Durum"] == "Kapalı"].copy()
            df_kap["sure"] = pd.to_numeric(df_kap.get("Çözüm Süresi (Dk)", pd.Series(dtype=float)), errors="coerce").fillna(0)
            ort_mttr = round(df_kap["sure"].mean(), 1) if not df_kap.empty else 0
            toplam_maliyet = pd.to_numeric(df.get("Toplam Maliyet (TL)", pd.Series(dtype=float)), errors="coerce").fillna(0).sum()

            try:
                if not df_kap.empty and "Kapatma Tarihi" in df_kap.columns:
                    df_kap["_t"] = pd.to_datetime(df_kap["Kapatma Tarihi"], format="%d/%m/%Y %H:%M", errors="coerce").dt.date
                    s7 = df_kap[df_kap["_t"] >= date.today() - timedelta(days=7)]
                    if not s7.empty:
                        makine_sayisi = max(s7["Makine"].nunique(), 1)
                        toplam_plan = 7 * 480 * makine_sayisi
                        toplam_dur  = s7["sure"].sum()
                        avail = round(max(0, min(100, (toplam_plan - toplam_dur) / toplam_plan * 100)), 1)
                    else:
                        avail = 100.0
                else:
                    avail = 100.0
            except:
                avail = 0.0

            avail_renk = "#4ade80" if avail >= 85 else "#FFD700" if avail >= 70 else "#E91E8C"
            mak_top = df["Makine"].value_counts().head(5)
            mak_max = max(mak_top.values) if len(mak_top) > 0 else 1
            onc_say = df[df["Durum"] == "Açık"]["Öncelik"].value_counts() if acik > 0 else pd.Series(dtype=int)

            df_tek = df_kap[df_kap["Müdahale Eden"].notna() & (df_kap["Müdahale Eden"] != "") & (df_kap["Müdahale Eden"] != "None")].copy() if "Müdahale Eden" in df_kap.columns else pd.DataFrame()
            tek_listesi = []
            if not df_tek.empty:
                for tek, grp in df_tek.groupby("Müdahale Eden"):
                    if tek and tek not in ["", "None", "nan"]:
                        sla_b = len(grp[grp["SLA Durumu"].str.contains("İçinde", na=False)]) if "SLA Durumu" in grp.columns else 0
                        sla_o = round(sla_b / max(len(grp), 1) * 100, 0)
                        ini   = "".join([w[0].upper() for w in tek.split()[:2]])
                        tek_listesi.append({"ad": tek, "ini": ini, "sayi": len(grp), "ort": round(grp["sure"].mean(), 0), "sla": sla_o})
                tek_listesi = sorted(tek_listesi, key=lambda x: x["sayi"], reverse=True)[:4]

            adf = df[df["Durum"] == "Açık"].copy()
            adf_rows = ""
            for _, r in adf.head(5).iterrows():
                sure_val = ""
                try:
                    ac = datetime.strptime(r.get("Açılış Tarihi", ""), "%d/%m/%Y %H:%M")
                    dk = int((datetime.now() - ac).total_seconds() / 60)
                    sure_val = f"{dk} dk"
                    sure_renk = "#E91E8C" if dk > 480 else "#FFD700"
                except:
                    sure_val = "—"
                    sure_renk = "#9B6FBF"

                onc = str(r.get("Öncelik", ""))
                if "KRİTİK" in onc:   tag_cls = "tag-red";    tag_txt = "KRİTİK"
                elif "YÜKSEK" in onc: tag_cls = "tag-yellow"; tag_txt = "YÜKSEK"
                elif "ORTA" in onc:   tag_cls = "tag-purple"; tag_txt = "ORTA"
                else:                 tag_cls = "tag-green";  tag_txt = "DÜŞÜK"

                adf_rows += f"""
                <div style="display:grid;grid-template-columns:90px 1fr 80px 90px 70px;gap:8px;font-size:11px;color:#E8D5FF;padding:7px 0;border-bottom:1px solid rgba(255,255,255,0.04);align-items:center;">
                  <div style="color:#FFD700;font-weight:700;">{r.get("Talep No", "")}</div>
                  <div>{str(r.get("Makine", ""))[:20]}</div>
                  <div><span style="border-radius:12px;padding:2px 8px;font-size:10px;font-weight:700;{'background:rgba(233,30,140,0.15);color:#E91E8C;border:1px solid rgba(233,30,140,0.3)' if tag_cls=='tag-red' else 'background:rgba(255,215,0,0.15);color:#FFD700;border:1px solid rgba(255,215,0,0.3)' if tag_cls=='tag-yellow' else 'background:rgba(155,111,191,0.15);color:#C89EE8;border:1px solid rgba(155,111,191,0.3)' if tag_cls=='tag-purple' else 'background:rgba(74,222,128,0.1);color:#4ade80;border:1px solid rgba(74,222,128,0.2)'};">{tag_txt}</span></div>
                  <div style="color:#9B6FBF;font-size:10px;">{str(r.get("Bölge", ""))[:12]}</div>
                  <div style="color:{sure_renk};font-weight:700;">{sure_val}</div>
                </div>"""

            tek_html = ""
            for t in tek_listesi:
                bar_w = min(int(t["sla"]), 100)
                tek_html += f"""
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
                  <div style="width:34px;height:34px;border-radius:50%;background:rgba(255,215,0,0.15);border:1px solid rgba(255,215,0,0.3);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;color:#FFD700;flex-shrink:0;">{t["ini"]}</div>
                  <div style="flex:1;min-width:0;">
                    <div style="font-size:12px;font-weight:600;color:#E8D5FF;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{t["ad"]}</div>
                    <div style="font-size:10px;color:#9B6FBF;">{t["sayi"]} arıza · Ort. {int(t["ort"])} dk</div>
                    <div style="background:rgba(255,255,255,0.05);border-radius:4px;height:4px;margin-top:4px;overflow:hidden;">
                      <div style="height:100%;border-radius:4px;background:linear-gradient(90deg,#7B00CC,#FFD700);width:{bar_w}%;"></div>
                    </div>
                  </div>
                  <div style="text-align:right;flex-shrink:0;">
                    <div style="font-size:14px;font-weight:800;color:#FFD700;">%{int(t["sla"])}</div>
                    <div style="font-size:10px;color:#9B6FBF;">SLA</div>
                  </div>
                </div>"""

            mak_html = ""
            colors = ["#FFD700", "#FFD700", "#E91E8C", "#E91E8C", "#C89EE8"]
            for i, (mak, val) in enumerate(mak_top.items()):
                w = int(val / mak_max * 100)
                renk = colors[min(i, 4)]
                mak_html += f"""
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                  <div style="font-size:10px;color:#9B6FBF;width:70px;text-align:right;flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{str(mak)[:10]}</div>
                  <div style="flex:1;background:rgba(255,255,255,0.05);border-radius:4px;height:20px;overflow:hidden;">
                    <div style="width:{w}%;height:100%;border-radius:4px;background:linear-gradient(90deg,#7B00CC,{renk});display:flex;align-items:center;justify-content:flex-end;padding-right:6px;">
                      <span style="font-size:10px;font-weight:700;color:#2D0052;">{val}</span>
                    </div>
                  </div>
                </div>"""

            sla_ic = round(sla_basari / 100 * 220, 1)
            sla_dis = round(220 - sla_ic, 1)
            avail_txt = "✅ Hedef üstü" if avail >= 85 else "⚠️ Geliştirilmeli"

            html_dashboard = """<style>
.dc{background:rgba(61,0,102,0.8);border:1px solid rgba(255,215,0,0.15);border-radius:10px;padding:16px;margin-bottom:0;}
.dt{font-size:12px;font-weight:700;color:#E8D5FF;margin-bottom:12px;}
.kpi-lbl{font-size:10px;color:#9B6FBF;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:6px;}
.kpi-val{font-size:32px;font-weight:800;line-height:1;}
.kpi-sub{font-size:11px;margin-top:5px;}
</style><div style="padding:4px 0;">
<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin-bottom:16px;">"""

            html_dashboard += f'<div class="dc" style="border-color:rgba(255,215,0,0.25);"><div class="kpi-lbl">📋 Toplam Talep</div><div class="kpi-val" style="color:#FFD700;">{toplam}</div><div class="kpi-sub" style="color:#4ade80;">+{bugun_s} bugün</div></div>'
            html_dashboard += f'<div class="dc" style="border-color:rgba(233,30,140,0.3);"><div class="kpi-lbl">🚨 Açık / Kritik</div><div class="kpi-val" style="color:#E91E8C;">{acik}</div><div class="kpi-sub" style="color:#E91E8C;">{kritik} kritik acil</div></div>'
            html_dashboard += f'<div class="dc"><div class="kpi-lbl">📈 Availability</div><div class="kpi-val" style="color:{avail_renk};">%{avail}</div><div class="kpi-sub" style="color:{avail_renk};">{avail_txt}</div></div>'
            html_dashboard += f'<div class="dc"><div class="kpi-lbl">⏱ Ort. MTTR</div><div class="kpi-val" style="color:#FFD700;">{int(ort_mttr)}<span style="font-size:14px;color:#9B6FBF;"> dk</span></div><div class="kpi-sub" style="color:#9B6FBF;">Ortalama tamir süresi</div></div>'
            html_dashboard += f'<div class="dc"><div class="kpi-lbl">💰 Toplam Maliyet</div><div style="font-size:24px;font-weight:800;color:#FFD700;line-height:1;">{toplam_maliyet:,.0f}<span style="font-size:12px;color:#9B6FBF;"> ₺</span></div><div class="kpi-sub" style="color:#9B6FBF;">SLA Uyum: %{sla_basari}</div></div>'
            html_dashboard += '</div>'
            html_dashboard += '<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:16px;">'
            html_dashboard += f'<div class="dc"><div class="dt">📊 Makine Bazlı Arıza (Top 5)</div>{mak_html}</div>'
            html_dashboard += f'<div class="dc"><div class="dt">⏱ SLA Performansı</div><div style="display:flex;align-items:center;gap:16px;"><svg width="90" height="90" viewBox="0 0 90 90"><circle cx="45" cy="45" r="35" fill="none" stroke="rgba(255,255,255,0.05)" stroke-width="16"/><circle cx="45" cy="45" r="35" fill="none" stroke="#FFD700" stroke-width="16" stroke-dasharray="{sla_ic} {sla_dis}" stroke-dashoffset="55" transform="rotate(-90 45 45)"/><text x="45" y="44" text-anchor="middle" font-size="13" font-weight="800" fill="#FFD700">%{sla_basari}</text><text x="45" y="57" text-anchor="middle" font-size="9" fill="#9B6FBF">SLA</text></svg><div><div style="margin-bottom:10px;"><div style="font-size:22px;font-weight:800;color:#4ade80;">{toplam-sla_asan}</div><div style="font-size:10px;color:#9B6FBF;">SLA İçinde</div></div><div><div style="font-size:22px;font-weight:800;color:#E91E8C;">{sla_asan}</div><div style="font-size:10px;color:#9B6FBF;">Aşıldı</div></div></div></div><div style="margin-top:12px;border-top:1px solid rgba(255,215,0,0.1);padding-top:10px;display:grid;grid-template-columns:1fr 1fr;gap:8px;text-align:center;"><div style="background:rgba(255,215,0,0.05);border-radius:8px;padding:8px;"><div style="font-size:18px;font-weight:800;color:#FFD700;">{kapali}</div><div style="font-size:10px;color:#9B6FBF;">Kapatılan</div></div><div style="background:rgba(233,30,140,0.05);border-radius:8px;padding:8px;"><div style="font-size:18px;font-weight:800;color:#E91E8C;">{acik}</div><div style="font-size:10px;color:#9B6FBF;">Açık</div></div></div></div>'
            html_dashboard += f'<div class="dc"><div class="dt">👨‍🔧 Teknisyen Performansı</div>{tek_html if tek_html else "<div style=\'font-size:12px;color:#9B6FBF;\'>Henüz veri yok.</div>"}</div>'
            html_dashboard += '</div>'

            krit_badge = f'<span style="background:rgba(233,30,140,0.15);color:#E91E8C;border:1px solid rgba(233,30,140,0.3);border-radius:12px;padding:2px 10px;font-size:11px;font-weight:700;margin-left:8px;">{kritik} KRİTİK</span>' if kritik > 0 else ""
            html_dashboard += f'<div class="dc" style="margin-bottom:16px;"><div class="dt" style="margin-bottom:10px;">🚨 Aktif Açık Talepler {krit_badge}</div><div style="display:grid;grid-template-columns:90px 1fr 80px 90px 70px;gap:8px;font-size:10px;color:#9B6FBF;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;padding-bottom:8px;border-bottom:1px solid rgba(255,215,0,0.1);margin-bottom:4px;"><div>Talep No</div><div>Makine</div><div>Öncelik</div><div>Bölge</div><div>Süre</div></div>{adf_rows if adf_rows else "<div style=\'font-size:13px;color:#4ade80;padding:12px 0;\'>✅ Açık talep bulunmuyor.</div>"}</div></div>'

            st.markdown(html_dashboard, unsafe_allow_html=True)

            try:
                df_bp = bakim_df_getir()
                if not df_bp.empty and "sonraki_bakim_tarihi" in df_bp.columns:
                    df_bp["_snr"] = pd.to_datetime(df_bp["sonraki_bakim_tarihi"], format="%d/%m/%Y", errors="coerce").dt.date
                    gec = df_bp[df_bp["durum"] == "Gecikmiş"]
                    yak = df_bp[(df_bp["_snr"] >= date.today()) & (df_bp["_snr"] <= date.today() + timedelta(days=7)) & (df_bp["durum"] == "Bekliyor")]
                    if not gec.empty:
                        st.error(f"🔴 {len(gec)} gecikmiş bakım var! Bakım Planları sekmesini kontrol edin.")
                    if not yak.empty:
                        st.warning(f"🟡 Bu hafta {len(yak)} bakım planlanmış: {', '.join(yak['makine'].tolist()[:3])}")
            except:
                pass


# =============================================================================
# SEKME 2: YENİ TALEP
# =============================================================================

with tab_yeni:
    st.markdown("### ➕ Yeni Arıza Bildirimi Oluştur")
    st.caption("Bu form tüm personele açıktır. Oturum açmadan da kullanılabilir.")

    if not st.session_state.get("_talep_gonderildi", False):
        st.session_state["bil_saat"] = datetime.now().strftime("%H:%M")
    else:
        st.session_state["_talep_gonderildi"] = False

    import base64, json as _json
    qr_params = st.query_params
    qr_makine = st.session_state.get("qr_makine", "")
    qr_bolge  = st.session_state.get("qr_bolge", "")
    if not qr_makine:
        try:
            d = qr_params.get("d", "")
            if d:
                veri = _json.loads(base64.urlsafe_b64decode(d + "==").decode())
                qr_makine = veri.get("makine", "")
                qr_bolge  = veri.get("bolge", "")
        except:
            pass

    bolge_index = 0
    if qr_bolge:
        for i, b in enumerate(BOLGELER):
            if qr_bolge.strip() in b or b in qr_bolge.strip():
                bolge_index = i
                break
    secili_bolge = st.selectbox("🏭 Tesis / Bölge *", BOLGELER, index=bolge_index)

    if qr_makine:
        st.info(f"📱 QR Kod ile bağlandınız — Makine: **{qr_makine}**")

    ariza_liste = aktif_ariza_turleri()
    ariza_tur   = st.selectbox("⚡ Arıza Kategorisi *", list(ariza_liste.keys()))
    alt_tur_listesi = ariza_liste.get(ariza_tur, ["Diğer"])
    alt_kategori    = st.selectbox("🔧 Alt Kategori *", alt_tur_listesi)

    with st.form("yeni_talep_formu", clear_on_submit=True):
        st.markdown("#### 👤 Bildiren Personel")
        bildiren      = st.text_input("Ad Soyad *", placeholder="Ahmet Yıldız")
        bildiren_dept = st.selectbox("Departman *", ["Üretim", "Depo", "Lojistik", "Bakım", "Kalite", "İdari", "Diğer"])
        vardiya       = st.selectbox("Vardiya *", ["Gündüz (08:00–16:00)", "Akşam (16:00–00:00)", "Gece (00:00–08:00)"])

        st.markdown(f"#### 🏭 Arıza Lokasyonu — {secili_bolge}")
        mak_liste = aktif_makine_listesi().get(secili_bolge, MAKINE_LISTESI_BOLGE[secili_bolge])
        mak_index = mak_liste.index(qr_makine) if qr_makine in mak_liste else 0
        makine    = st.selectbox("Makine / Sistem *", mak_liste, index=mak_index)
        oncelik   = st.selectbox("🚨 Kritiklik Seviyesi (SLA) *", list(ARIZA_ONCELIKLERI.keys()))
        bildirim_saat = st.text_input("🕐 Arıza Fark Edilme Saati", value=st.session_state.get("bil_saat", datetime.now().strftime("%H:%M")), help="SS:DD formatında")

        st.markdown(f"""
        <div style="background:rgba(61,0,102,0.6);border:1px solid rgba(255,215,0,0.2);border-radius:8px;padding:10px 14px;font-size:13px;margin:4px 0;">
          ⚡ <strong style="color:#FFD700;">{ariza_tur}</strong> &nbsp;›&nbsp; <span style="color:#C89EE8;">{alt_kategori}</span>
        </div>""", unsafe_allow_html=True)

        ariza_tanimi = st.text_area("📝 Arıza Tanımı *", placeholder="Arızanın belirti ve etkilerini açıklayın...", height=120)
        foto_notu    = st.text_input("📎 Fotoğraf / Referans Notu", placeholder="Opsiyonel")

        sla_bilgi = ARIZA_ONCELIKLERI[oncelik]
        st.markdown(f"""
        <div style="background:rgba(61,0,102,0.6);border:1px solid rgba(255,215,0,0.15);border-radius:8px;padding:12px 16px;margin:8px 0;font-size:12px;">
          🏭 <strong style="color:#FFD700;">Bölge:</strong> <span style="color:#E8D5FF;">{secili_bolge}</span>
          &nbsp;&nbsp;|&nbsp;&nbsp;
          ⏱ <strong style="color:#FFD700;">SLA Hedefi:</strong> <strong style="color:#4ade80;">{sla_bilgi["sla_dk"]} dakika</strong>
        </div>""", unsafe_allow_html=True)

        submit_yeni = st.form_submit_button("🚀 Arıza Talebi Oluştur", use_container_width=True)

        if submit_yeni:
            if not bildiren.strip():
                st.error("❌ Ad Soyad zorunludur.")
            elif not ariza_tanimi.strip():
                st.error("❌ Arıza Tanımı zorunludur.")
            else:
                no = talep_no_uret()
                ok = sb_insert("ariza_kayitlari", {
                    "talep_no": no, "bolge": secili_bolge, "durum": "Açık",
                    "oncelik": oncelik, "vardiya": vardiya,
                    "acilis_tarihi": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "kapatma_tarihi": "", "bildiren": bildiren.strip(),
                    "bildiren_departman": bildiren_dept, "mudahale_eden": "",
                    "makine": makine, "ariza_turu": ariza_tur, "alt_kategori": alt_kategori,
                    "ariza_tanimi": ariza_tanimi.strip(),
                    "bildirim_saati": bildirim_saat.strip(),
                    "ilk_mudahale_saati": "", "cozum_suresi_dk": 0,
                    "sla_durumu": "Açık — Süre Devam Ediyor",
                    "cozum_aciklamasi": "", "kok_neden": "", "bes_neden_analizi": "",
                    "kaizen_onerisi": "", "kullanilan_malzemeler": "",
                    "malzeme_maliyeti": 0, "isguc_maliyeti": 0, "toplam_maliyet": 0,
                    "fotograf_notu": foto_notu, "kapatma_onayi": ""
                })
                if ok:
                    cache_temizle()
                    st.session_state["_talep_gonderildi"] = True
                    log_yaz("YENİ TALEP", f"{no} — {secili_bolge} — {makine} — {bildiren}")
                    if "KRİTİK" in oncelik or "YÜKSEK" in oncelik:
                        email_gonder(
                            f"🚨 {oncelik[:10]} Arıza — {makine} ({secili_bolge})",
                            f"Talep No: {no}\nBölge: {secili_bolge}\nMakine: {makine}\nÖncelik: {oncelik}\nTanım: {ariza_tanimi.strip()}\nBildiren: {bildiren.strip()}",
                            kategori="kritik_ariza"
                        )
                    st.success(f"✅ Talep **{no}** oluşturuldu! Bölge: {secili_bolge} | SLA: {sla_bilgi['sla_dk']} dk")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Kayıt başarısız. Supabase bağlantısını kontrol edin.")


# =============================================================================
# SEKME 3: TALEP KAPAT
# =============================================================================

with tab_kapat:
    if not giris_gerektir("Teknisyen"):
        pass
    else:
        df_k = ariza_df_getir()
        if df_k.empty or "Durum" not in df_k.columns:
            st.success("🎉 Müdahale bekleyen açık talep bulunmuyor.")
        else:
            acik_k = df_k[df_k["Durum"] == "Açık"].copy()
            if acik_k.empty:
                st.success("🎉 Müdahale bekleyen açık talep bulunmuyor. Harika iş!")
            else:
                bf = st.selectbox("🏭 Bölge Filtresi", ["Tüm Bölgeler"] + BOLGELER, key="kapat_bolge")
                if bf != "Tüm Bölgeler" and "Bölge" in acik_k.columns:
                    acik_k = acik_k[acik_k["Bölge"] == bf]

                if acik_k.empty:
                    st.info(f"ℹ️ {bf} bölgesinde açık talep bulunmuyor.")
                else:
                    krit_k = acik_k[acik_k["Öncelik"].str.startswith("🔴", na=False)]
                    if not krit_k.empty:
                        st.markdown(f'''<div class="kritik-banner"><strong style="color:#f87171;">🚨 {len(krit_k)} KRİTİK ARIZA — Acil müdahale bekliyor</strong></div>''', unsafe_allow_html=True)

                    col_s1, _ = st.columns([3, 1])
                    with col_s1:
                        secenekler = acik_k.apply(
                            lambda r: f"[{r['Talep No']}] {str(r.get('Bölge',''))[:10]} | {r['Öncelik'][:2]} {r['Makine']} — {str(r['Arıza Tanımı'])[:50]}",
                            axis=1
                        ).tolist()
                        secilen = st.selectbox("📋 Kapatılacak Talebi Seçin", secenekler)

                    secilen_no = secilen.split("]")[0].replace("[", "").strip()
                    talep_df2  = df_k[df_k["Talep No"] == secilen_no]
                    if talep_df2.empty:
                        st.error("Talep bulunamadı.")
                        st.stop()
                    talep = talep_df2.iloc[0]

                    sla_g   = sla_hesapla(talep["Öncelik"], talep["Açılış Tarihi"])
                    sla_cls = "sla-ok" if "İçinde" in sla_g["durum"] else "sla-warn"
                    st.markdown(f"""
                    <div class="durum-karti">
                      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
                        <div>
                          <span style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;">TALEP DETAYI</span>
                          <div style="font-size:20px;font-weight:700;color:#e2e8f0;margin-top:4px;">{talep["Talep No"]}</div>
                        </div>
                        <span class="sla-badge {sla_cls}">{sla_g["durum"]}</span>
                      </div>
                      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;font-size:13px;">
                        <div><span style="color:#64748b;">Bölge</span><br><strong style="color:#fbbf24;">{talep.get("Bölge","—")}</strong></div>
                        <div><span style="color:#64748b;">Makine</span><br><strong style="color:#e2e8f0;">{talep["Makine"]}</strong></div>
                        <div><span style="color:#64748b;">Bildiren</span><br><strong style="color:#e2e8f0;">{talep["Bildiren"]}</strong></div>
                        <div><span style="color:#64748b;">Açılış</span><br><strong style="color:#e2e8f0;">{talep["Açılış Tarihi"]}</strong></div>
                        <div><span style="color:#64748b;">Geçen</span><br><strong style="color:#fbbf24;">{sla_g["gecen_dk"]} dk / {sla_g["sla_dk"]} dk SLA</strong></div>
                        <div><span style="color:#64748b;">SLA</span><br><strong style="color:#{"f87171" if sla_g["oran"]>100 else "4ade80"};">%{sla_g["oran"]}</strong></div>
                      </div>
                      <div style="margin-top:12px;padding-top:10px;border-top:1px solid rgba(99,179,237,0.1);font-size:13px;color:#94a3b8;">
                        📝 <em>{talep["Arıza Tanımı"]}</em>
                      </div>
                    </div>""", unsafe_allow_html=True)

                    st.markdown("#### 🔧 Müdahale & Çözüm Bilgileri")
                    ISCI_UCRET = 300

                    tum_tamam = True
                    if "Periyodik Bakım" in str(talep.get("Arıza Tanımı", "")):
                        st.markdown("#### ☑️ Bakım Kontrol Listesi")
                        try:
                            makine_adi = talep.get("Makine", "")
                            tum_bp     = sb_select("bakim_plani")
                            bp_rows    = [r for r in tum_bp if r.get("makine", "") == makine_adi]
                            bp_gecik   = [r for r in bp_rows if r.get("durum") == "Gecikmiş"]
                            if bp_gecik:
                                bp_rows = bp_gecik
                            if bp_rows:
                                bp_id    = bp_rows[0]["id"]
                                maddeler = checklist_getir(bp_id)
                                if maddeler:
                                    mevcut_kayitlar  = checklist_kayit_getir(talep["Talep No"])
                                    madde_adlari     = {m["madde"] for m in maddeler}
                                    tamamli_maddeler = {k["madde"] for k in mevcut_kayitlar if k.get("tamamlandi") and k["madde"] in madde_adlari}
                                    tum_tamam        = len(tamamli_maddeler) >= len(maddeler)
                                    teknisyen_adi    = st.session_state.get("aktif_tam_ad", "")
                                    progress = min(len(tamamli_maddeler) / max(len(maddeler), 1), 1.0)
                                    renk = "#16A34A" if tum_tamam else "#D97706"
                                    st.markdown(f"""
                                    <div style="background:rgba(30,41,59,0.6);border:1px solid rgba(99,179,237,0.2);border-radius:10px;padding:14px 16px;margin-bottom:12px;">
                                      <div style="display:flex;justify-content:space-between;margin-bottom:8px;">
                                        <span style="font-size:13px;font-weight:600;color:#e2e8f0;">☑️ Kontrol Listesi</span>
                                        <span style="font-size:13px;font-weight:700;color:{renk};">{len(tamamli_maddeler)}/{len(maddeler)} Tamamlandı</span>
                                      </div>
                                      <div style="background:rgba(15,23,42,0.5);border-radius:6px;height:8px;">
                                        <div style="background:{renk};width:{int(progress*100)}%;height:8px;border-radius:6px;"></div>
                                      </div>
                                    </div>""", unsafe_allow_html=True)

                                    with st.form(f"checklist_form_{talep['Talep No']}"):
                                        st.markdown("**Tamamlanan maddeleri işaretleyin:**")
                                        chk_degerleri = {}
                                        not_degerleri = {}
                                        for m in maddeler:
                                            zaten_tamam = m["madde"] in tamamli_maddeler
                                            mevcut_k    = next((k for k in mevcut_kayitlar if k["madde"] == m["madde"]), None)
                                            not_val     = mevcut_k.get("not_", "") if mevcut_k else ""
                                            yapan       = mevcut_k.get("yapan", "") if mevcut_k else ""
                                            durum_ikon  = "✅" if zaten_tamam else "⬜"
                                            col_ck1, col_ck2, col_ck3 = st.columns([3, 3, 1])
                                            m_id = m["id"]
                                            with col_ck1:
                                                chk_degerleri[m_id] = st.checkbox(f"{durum_ikon} **{m['sira']}.** {m['madde']}", value=zaten_tamam, key=f"chk_{talep['Talep No']}_{m_id}")
                                            with col_ck2:
                                                not_degerleri[m_id] = st.text_input("Not", value=not_val, placeholder="Not ekle...", key=f"not_{talep['Talep No']}_{m_id}", label_visibility="collapsed")
                                            with col_ck3:
                                                if zaten_tamam and yapan:
                                                    st.caption(f"👤 {yapan}")

                                        kaydet_btn = st.form_submit_button("💾 Checklist Kaydet", use_container_width=True)
                                        if kaydet_btn:
                                            zaman_str = datetime.now().strftime("%d/%m/%Y %H:%M")
                                            basari = True
                                            for m in maddeler:
                                                m_id    = m["id"]
                                                chk_val = chk_degerleri.get(m_id, chk_degerleri.get(str(m_id), False))
                                                not_val2 = not_degerleri.get(m_id, not_degerleri.get(str(m_id), ""))
                                                mevcut_k = next((k for k in mevcut_kayitlar if k["madde"] == m["madde"]), None)
                                                if mevcut_k:
                                                    ok = sb_update("bakim_checklist_kayit", f"id=eq.{mevcut_k['id']}", {"tamamlandi": chk_val, "yapan": teknisyen_adi if chk_val else "", "zaman": zaman_str if chk_val else "", "not_": not_val2})
                                                else:
                                                    ok = sb_insert("bakim_checklist_kayit", {"ariza_talep_no": talep["Talep No"], "bakim_plani_id": bp_id, "madde": m["madde"], "tamamlandi": chk_val, "yapan": teknisyen_adi if chk_val else "", "zaman": zaman_str if chk_val else "", "not_": not_val2})
                                                if not ok:
                                                    basari = False
                                            if basari:
                                                st.success("✅ Checklist kaydedildi!")
                                            else:
                                                st.error("❌ Bazı maddeler kaydedilemedi.")
                                            time.sleep(0.8)
                                            st.rerun()

                                    if not tum_tamam:
                                        st.warning(f"⚠️ Tüm maddeler tamamlanmadan talep kapatılamaz! ({len(tamamli_maddeler)}/{len(maddeler)})")
                                    else:
                                        st.success("✅ Tüm kontrol maddeleri tamamlandı!")
                        except Exception as e:
                            st.caption(f"Checklist yüklenemedi: {e}")

                    st.markdown("##### 👤 Teknisyen & Zaman")
                    col_k1, col_k2, col_k3 = st.columns(3)
                    with col_k1:
                        mudahale_eden_dis = st.text_input("Müdahale Eden Teknisyen *", value=st.session_state.get("aktif_tam_ad", ""), key="mud_eden_dis")
                    with col_k2:
                        mud_bas_time = st.time_input("🕐 Müdahaleye Başlama", value=datetime.now().time(), key="mud_bas_time")
                    with col_k3:
                        mud_bit_time = st.time_input("🕑 Arıza Giderilme", value=datetime.now().time(), key="mud_bit_time")

                    try:
                        bugun_d = date.today()
                        bd  = datetime.combine(bugun_d, mud_bas_time)
                        btt = datetime.combine(bugun_d, mud_bit_time)
                        if btt <= bd:
                            btt += timedelta(days=1)
                        cozum_dk = max(1, int((btt - bd).total_seconds() / 60))
                    except:
                        cozum_dk = 1

                    try:
                        acilis_dt  = datetime.strptime(talep["Açılış Tarihi"], "%d/%m/%Y %H:%M")
                        bekleme_dk = max(0, int((bd - acilis_dt).total_seconds() / 60))
                        toplam_dk  = max(0, int((btt - acilis_dt).total_seconds() / 60))
                    except:
                        bekleme_dk = 0
                        toplam_dk  = cozum_dk

                    isguc   = round((cozum_dk / 60) * ISCI_UCRET, 2)
                    mud_bas = mud_bas_time.strftime("%H:%M")
                    mud_bit = mud_bit_time.strftime("%H:%M")

                    st.markdown(f"""
                    <div style="background:rgba(61,0,102,0.6);border:1px solid rgba(255,215,0,0.2);border-radius:10px;padding:14px 16px;margin:8px 0 16px 0;">
                      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;text-align:center;">
                        <div><div style="font-size:10px;color:#9B6FBF;text-transform:uppercase;margin-bottom:4px;">⚙️ Müdahale Süresi</div><div style="font-size:22px;font-weight:800;color:#FFD700;">{cozum_dk} dk</div><div style="font-size:10px;color:#9B6FBF;">{mud_bas} → {mud_bit}</div></div>
                        <div><div style="font-size:10px;color:#9B6FBF;text-transform:uppercase;margin-bottom:4px;">⏳ Bekleme Süresi</div><div style="font-size:22px;font-weight:800;color:#C89EE8;">{bekleme_dk} dk</div><div style="font-size:10px;color:#9B6FBF;">Açılış → Müdahale</div></div>
                        <div><div style="font-size:10px;color:#9B6FBF;text-transform:uppercase;margin-bottom:4px;">📊 Toplam Süre</div><div style="font-size:22px;font-weight:800;color:#E8D5FF;">{toplam_dk} dk</div><div style="font-size:10px;color:#9B6FBF;">Açılış → Kapanış</div></div>
                        <div><div style="font-size:10px;color:#9B6FBF;text-transform:uppercase;margin-bottom:4px;">💰 İş Gücü</div><div style="font-size:22px;font-weight:800;color:#4ade80;">{isguc:,.0f} ₺</div><div style="font-size:10px;color:#9B6FBF;">300 ₺/saat</div></div>
                      </div>
                    </div>""", unsafe_allow_html=True)

                    with st.form("kapat_formu"):
                        mudahale_eden = st.text_input("Müdahale Eden Teknisyen *", value=mudahale_eden_dis, key="mud_eden_form")
                        kok_neden     = st.selectbox("🔍 Kök Neden", ["Yağlama eksikliği", "Aşınma (ömür tükenmesi)", "Hatalı kullanım", "Yetersiz bakım periyodu", "Tasarım/malzeme yetersizliği", "Dış etken (toz, nem, darbe)", "Yazılım/donanım arızası", "Bilinmiyor", "Diğer"])
                        kapat_onayi   = st.selectbox("✅ Kapatma Onayı", ["Teknisyen Onayı", "Vardiya Amiri Onayı", "Bakım Müdürü Onayı"])
                        cozum_aciklama = st.text_area("Uygulanan Çözüm & Teknik Notlar *", height=90)
                        neden_analizi  = st.text_area("5 Neden Analizi", height=90)
                        kaizen         = st.text_area("Kaizen / İyileştirme Önerisi", height=70)

                        st.markdown("#### 📦 Kullanılan Malzeme")
                        df_stok_k  = stok_df_getir()
                        stok_sec   = ["—  Malzeme Kullanılmadı"]
                        if not df_stok_k.empty and "Malzeme Adı" in df_stok_k.columns:
                            stok_sec += df_stok_k["Malzeme Adı"].tolist()
                        malzeme_secim   = st.selectbox("📦 Stoktan Malzeme", stok_sec)
                        malzeme_adet    = st.number_input("Kullanılan Miktar", min_value=0, step=1, value=0)
                        malzeme_maliyet = st.number_input("Malzeme Maliyeti (TL)", min_value=0, step=50, value=0)

                        submit_kapat = st.form_submit_button("✅ Talebi Kapat & Kaydet", use_container_width=True)

                        if submit_kapat:
                            if not mudahale_eden.strip():
                                st.error("❌ Teknisyen adı zorunludur.")
                            elif not cozum_aciklama.strip():
                                st.error("❌ Çözüm açıklaması zorunludur.")
                            elif not tum_tamam:
                                st.error("❌ Tüm checklist maddeleri tamamlanmadan talep kapatılamaz!")
                            else:
                                malzeme_metni = "—"
                                if "—" not in malzeme_secim and malzeme_adet > 0 and not df_stok_k.empty:
                                    stok_satir = df_stok_k[df_stok_k["Malzeme Adı"] == malzeme_secim]
                                    if not stok_satir.empty:
                                        stok_mik = int(stok_satir["Stok Miktarı"].values[0])
                                        if stok_mik < malzeme_adet:
                                            st.error(f"❌ Yetersiz stok! Mevcut: {stok_mik}")
                                            st.stop()
                                        sb_update("stok", f"malzeme_adi=eq.{malzeme_secim}", {"stok_miktari": stok_mik - malzeme_adet, "son_guncelleme": datetime.now().strftime("%d/%m/%Y")})
                                    malzeme_metni = f"{malzeme_secim} x {malzeme_adet}"

                                toplam_maliyet_k = isguc + malzeme_maliyet
                                kapat_zaman = datetime.now().strftime("%d/%m/%Y %H:%M")
                                sla_s = sla_hesapla(talep["Öncelik"], talep["Açılış Tarihi"], kapat_zaman)

                                sb_update("ariza_kayitlari", f"talep_no=eq.{secilen_no}", {
                                    "durum": "Kapalı", "kapatma_tarihi": kapat_zaman,
                                    "mudahale_eden": mudahale_eden.strip(),
                                    "ilk_mudahale_saati": f"{mud_bas} - {mud_bit}",
                                    "cozum_suresi_dk": int(cozum_dk), "sla_durumu": sla_s["durum"],
                                    "cozum_aciklamasi": cozum_aciklama.strip(), "kok_neden": str(kok_neden),
                                    "bes_neden_analizi": neden_analizi, "kaizen_onerisi": kaizen,
                                    "kullanilan_malzemeler": malzeme_metni,
                                    "malzeme_maliyeti": float(malzeme_maliyet),
                                    "isguc_maliyeti": float(isguc), "toplam_maliyet": float(toplam_maliyet_k),
                                    "kapatma_onayi": str(kapat_onayi),
                                })
                                cache_temizle()
                                log_yaz("TALEP KAPATILDI", f"{secilen_no} — {mudahale_eden} — {cozum_dk} dk — {toplam_maliyet_k:.0f} TL")
                                if "KRİTİK" in str(talep.get("Öncelik", "")) or "YÜKSEK" in str(talep.get("Öncelik", "")):
                                    email_gonder(
                                        f"✅ Talep Kapatıldı — {talep.get('Makine', '')}",
                                        f"Talep No: {secilen_no}\nMakine: {talep.get('Makine','')}\nSüre: {cozum_dk} dk\nSLA: {sla_s['durum']}\nMaliyet: {toplam_maliyet_k:,.0f} TL",
                                        kategori="talep_kapatma"
                                    )
                                st.success(f"✅ Talep **{secilen_no}** kapatıldı! Süre: {cozum_dk} dk | Toplam: {toplam_maliyet_k:,.0f} TL | {sla_s['durum']}")
                                time.sleep(1.5)
                                st.rerun()


# =============================================================================
# SEKME 4: RAPORLAMA
# =============================================================================

with tab_rapor:
    if not giris_gerektir("Teknisyen"):
        pass
    else:
        st.markdown("### 📋 Arıza Arşivi & Raporlama")
        df_r = ariza_df_getir()

        with st.expander("🔍 Filtrele & Ara", expanded=True):
            col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
            with col_f1: f_bolge   = st.selectbox("Bölge",      ["Tümü"] + BOLGELER)
            with col_f2: f_durum   = st.selectbox("Durum",      ["Tümü", "Açık", "Kapalı"])
            with col_f3: f_oncelik = st.selectbox("Öncelik",    ["Tümü"] + list(ARIZA_ONCELIKLERI.keys()))
            with col_f4: f_makine  = st.selectbox("Makine",     ["Tümü"] + MAKINE_LISTESI)
            with col_f5: f_tur     = st.selectbox("Arıza Türü", ["Tümü"] + list(ARIZA_TURLERI.keys()))
            col_t1, col_t2, col_t3 = st.columns([2, 2, 2])
            with col_t1: f_bas   = st.date_input("Başlangıç", date(2025, 1, 1))
            with col_t2: f_bit   = st.date_input("Bitiş", date.today())
            with col_t3: f_arama = st.text_input("🔍 Metin Ara", placeholder="Talep no, personel, makine...")

        if df_r.empty or "Durum" not in df_r.columns:
            st.info("📭 Henüz arıza kaydı bulunmuyor.")
        else:
            g = df_r.copy()
            if f_bolge   != "Tümü" and "Bölge"     in g.columns: g = g[g["Bölge"]     == f_bolge]
            if f_durum   != "Tümü" and "Durum"      in g.columns: g = g[g["Durum"]      == f_durum]
            if f_oncelik != "Tümü" and "Öncelik"    in g.columns: g = g[g["Öncelik"]    == f_oncelik]
            if f_makine  != "Tümü" and "Makine"     in g.columns: g = g[g["Makine"]     == f_makine]
            if f_tur     != "Tümü" and "Arıza Türü" in g.columns: g = g[g["Arıza Türü"] == f_tur]
            if f_arama.strip():
                try:
                    mask = g.apply(lambda r: r.astype(str).str.contains(f_arama, case=False, na=False).any(), axis=1)
                    g = g[mask]
                except:
                    pass
            try:
                if "Açılış Tarihi" in g.columns:
                    g["_t"] = pd.to_datetime(g["Açılış Tarihi"], format="%d/%m/%Y %H:%M", errors="coerce").dt.date
                    g = g[(g["_t"] >= f_bas) & (g["_t"] <= f_bit)].drop(columns=["_t"])
            except:
                pass

            col_oz1, col_oz2, col_oz3, col_oz4 = st.columns(4)
            with col_oz1: st.metric("Kayıt Sayısı", len(g))
            with col_oz2:
                try: os_ = round(pd.to_numeric(g["Çözüm Süresi (Dk)"], errors="coerce").dropna().mean())
                except: os_ = "—"
                st.metric("Ort. Çözüm Süresi", f"{os_} dk" if isinstance(os_, (int, float)) else "—")
            with col_oz3:
                try: tm = pd.to_numeric(g["Toplam Maliyet (TL)"], errors="coerce").sum()
                except: tm = 0
                st.metric("Toplam Maliyet", f"{tm:,.0f} ₺")
            with col_oz4:
                try: sa = len(g[g["SLA Durumu"].str.contains("Aşıldı", na=False)])
                except: sa = 0
                st.metric("SLA Aşımı", sa)

            col_dl1, _ = st.columns([1, 4])
            with col_dl1:
                st.download_button("📥 CSV İndir",
                    g.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                    file_name=f"ariza_raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv")

            if not g.empty:
                try:
                    if "Açılış Tarihi" in g.columns:
                        st.dataframe(g.sort_values("Açılış Tarihi", ascending=False), use_container_width=True, hide_index=True)
                    else:
                        st.dataframe(g, use_container_width=True, hide_index=True)
                except:
                    st.dataframe(g, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("#### 📐 Makine Bazlı MTTR & MTBF Özeti")
            try:
                df_kapali = g[g["Durum"] == "Kapalı"].copy() if "Durum" in g.columns else pd.DataFrame()
                if not df_kapali.empty and "Çözüm Süresi (Dk)" in df_kapali.columns:
                    df_kapali["sure"] = pd.to_numeric(df_kapali["Çözüm Süresi (Dk)"], errors="coerce")
                    df_kapali = df_kapali.dropna(subset=["sure", "Makine"])
                    if not df_kapali.empty:
                        ozet_rows = []
                        for makine_adi, grp in df_kapali.groupby("Makine"):
                            mttr = round(grp["sure"].mean(), 1)
                            toplam = len(grp)
                            mtbf_dk = avail = None
                            if "Kapatma Tarihi" in grp.columns and toplam >= 2:
                                grp2 = grp.copy()
                                grp2["kap"] = pd.to_datetime(grp2["Kapatma Tarihi"], format="%d/%m/%Y %H:%M", errors="coerce")
                                grp2 = grp2.dropna(subset=["kap"]).sort_values("kap")
                                if len(grp2) >= 2:
                                    fark = grp2["kap"].diff().dropna()
                                    mtbf_dk = round(fark.dt.total_seconds().mean() / 60, 1)
                                    avail = round(mtbf_dk / (mtbf_dk + mttr) * 100, 1)
                            ozet_rows.append({"Makine": makine_adi, "Arıza Sayısı": toplam, "MTTR (dk)": mttr, "MTBF (dk)": mtbf_dk if mtbf_dk else "—", "Availability (%)": avail if avail else "—"})
                        df_ozet = pd.DataFrame(ozet_rows).sort_values("Arıza Sayısı", ascending=False)
                        st.dataframe(df_ozet, use_container_width=True, hide_index=True)
                        en_kotu = df_ozet.iloc[0]
                        st.info(f"⚠️ En fazla arıza: **{en_kotu['Makine']}** — {en_kotu['Arıza Sayısı']} arıza | MTTR: {en_kotu['MTTR (dk)']} dk")
            except Exception as e:
                st.caption(f"MTTR/MTBF hesaplanamadı: {e}")

# =============================================================================
# SEKME 5: STOK YÖNETİMİ
# =============================================================================

with tab_stok:
    if not giris_gerektir("Teknisyen"):
        pass
    else:
        st.markdown("### 📦 Yedek Parça & Sarf Malzeme Stok Yönetimi")
        df_st = stok_df_getir()

        if df_st.empty or "Malzeme Adı" not in df_st.columns:
            st.info("📦 Stok verisi yükleniyor veya henüz kayıt yok.")
        else:
            df_st["Stok Miktarı"]  = pd.to_numeric(df_st["Stok Miktarı"], errors="coerce").fillna(0)
            df_st["Kritik Seviye"] = pd.to_numeric(df_st["Kritik Seviye"], errors="coerce").fillna(0)
            kritik_stok = df_st[df_st["Stok Miktarı"] <= df_st["Kritik Seviye"]]
            for _, row in kritik_stok.iterrows():
                st.markdown(f'''<div class="kritik-banner">⚠️ <strong style="color:#fbbf24;">ACİL SİPARİŞ:</strong> <span style="color:#cbd5e1;">{row["Malzeme Adı"]}</span> — Mevcut: <strong style="color:#f87171;">{row["Stok Miktarı"]} {row.get("Birim","adet")}</strong> / Kritik: {row["Kritik Seviye"]}</div>''', unsafe_allow_html=True)

            if df_st["Maksimum Stok"].sum() > 0:
                df_st2 = df_st.copy()
                df_st2["Doluluk %"] = (pd.to_numeric(df_st2["Stok Miktarı"], errors="coerce").fillna(0) / pd.to_numeric(df_st2["Maksimum Stok"], errors="coerce").replace(0, 1).fillna(1) * 100).round(1).clip(upper=100)
                st.markdown("#### Stok Doluluk Oranları")
                st.bar_chart(df_st2.set_index("Malzeme Adı")["Doluluk %"], height=240)

            col_tbl, col_form = st.columns([3, 2])
            with col_tbl:
                st.markdown("#### Güncel Envanter Tablosu")
                gsc = [s for s in STOK_SUTUNLARI if s in df_st.columns]
                st.dataframe(df_st[gsc], use_container_width=True, hide_index=True)
                st.download_button("📥 Envanter İndir", df_st.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), file_name=f"stok_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

            with col_form:
                st.markdown("#### 🔧 Stok Güncelle")
                with st.form("stok_guncelle"):
                    secilen_mal = st.selectbox("Malzeme", df_st["Malzeme Adı"].tolist())
                    islem_tipi  = st.radio("İşlem", ["Stok Girişi (Ekleme)", "Stok Çıkışı (Kullanım)", "Mutlak Değer Gir"])
                    miktar      = st.number_input("Miktar", min_value=0, step=1, value=0)
                    st.text_input("Not", placeholder="Opsiyonel")
                    if st.form_submit_button("💾 Kaydet", use_container_width=True):
                        ds2  = stok_df_getir()
                        ms2  = ds2["Malzeme Adı"] == secilen_mal
                        mev  = int(ds2.loc[ms2, "Stok Miktarı"].values[0])
                        if "Ekleme" in islem_tipi: yeni_m = mev + miktar
                        elif "Çıkış" in islem_tipi:
                            if mev < miktar: st.error(f"❌ Yetersiz stok! Mevcut:{mev}"); st.stop()
                            yeni_m = mev - miktar
                        else: yeni_m = miktar
                        sb_update("stok", f"malzeme_adi=eq.{secilen_mal}", {"stok_miktari": int(yeni_m), "son_guncelleme": datetime.now().strftime("%d/%m/%Y")})
                        cache_temizle()
                        log_yaz("STOK GÜNCELLEME", f"{secilen_mal} {mev}→{yeni_m}")
                        try:
                            ds_check = stok_df_getir()
                            satir = ds_check[ds_check["Malzeme Adı"] == secilen_mal]
                            if not satir.empty:
                                krit_sev = int(satir["Kritik Seviye"].values[0])
                                if yeni_m <= krit_sev:
                                    email_gonder(f"⚠️ Kritik Stok — {secilen_mal}", f"Mevcut: {yeni_m} | Kritik: {krit_sev}", kategori="stok_uyari")
                        except:
                            pass
                        st.success(f"✅ {secilen_mal}: {mev} → **{yeni_m}**")
                        time.sleep(1)
                        st.rerun()

                if yetkili_mi("Yönetici"):
                    st.markdown("---")
                    st.markdown("#### ➕ Yeni Malzeme Tanımla")
                    with st.form("yeni_malzeme"):
                        col_nm1, col_nm2 = st.columns(2)
                        with col_nm1:
                            y_kod  = st.text_input("Malzeme Kodu", placeholder="M009")
                            y_ad   = st.text_input("Malzeme Adı")
                            y_kat  = st.selectbox("Kategori", ["Hareketli Parça", "Sensör", "Elektrik", "Mekanik", "Sarf", "Hidrolik", "Elektronik", "Diğer"])
                            y_bir  = st.selectbox("Birim", ["Adet", "Litre", "Metre", "Kg", "Rulo", "Kutu", "Set", "Takım"])
                        with col_nm2:
                            y_stok  = st.number_input("Başlangıç Stok", min_value=0, step=1)
                            y_krit  = st.number_input("Kritik Seviye",  min_value=0, step=1)
                            y_maks  = st.number_input("Maksimum Stok",  min_value=0, step=1)
                            y_fiyat = st.number_input("Son Fiyat (TL)", min_value=0, step=10)
                        y_tedarik = st.text_input("Tedarikçi")
                        if st.form_submit_button("✅ Malzeme Ekle", use_container_width=True) and y_ad.strip():
                            ds3 = stok_df_getir()
                            if y_kod and not ds3.empty and y_kod in ds3["Malzeme Kodu"].values:
                                st.error("❌ Bu kod zaten mevcut!")
                            else:
                                sb_insert("stok", {"malzeme_kodu": y_kod, "malzeme_adi": y_ad.strip(), "kategori": y_kat, "birim": y_bir, "stok_miktari": int(y_stok), "kritik_seviye": int(y_krit), "maksimum_stok": int(y_maks), "son_fiyat": float(y_fiyat), "tedarikci": y_tedarik, "son_guncelleme": datetime.now().strftime("%d/%m/%Y")})
                                cache_temizle()
                                log_yaz("YENİ MALZEME", f"{y_kod} — {y_ad}")
                                st.success(f"✅ {y_ad} eklendi!")
                                time.sleep(1)
                                st.rerun()


# =============================================================================
# BAKIMPLANLARI — Sabitler
# =============================================================================

PERIYOTLAR = {"Günlük": 1, "Haftalık": 7, "Aylık": 30, "3 Aylık": 90, "6 Aylık": 180, "Yıllık": 365}
BAKIM_TURLERI = ["Yağlama & Gres", "Fren Testi", "Rulman Kontrolü", "Elektrik Bağlantı Kontrolü", "Sensör Kalibrasyonu", "Filtre Değişimi", "Mekanik Bağlantı Kontrolü", "Hidrolik Yağ Kontrolü", "Akü / Şarj Kontrolü", "Genel Revizyon", "Temizlik & İnspeksiyon", "Diğer"]

@st.cache_data(ttl=30)
def bakim_df_getir():
    try:
        rows = sb_select("bakim_plani")
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df = df.drop(columns=[c for c in ["created_at"] if c in df.columns])
        return df
    except Exception:
        return pd.DataFrame()

# =============================================================================
# SEKME 6: BAKIM PLANLARI
# =============================================================================

with tab_bakim:
    if not giris_gerektir("Yönetici"):
        pass
    else:
        st.markdown("### 🔧 Periyodik Bakım Planları")
        df_bakim = bakim_df_getir()

        col_b1, col_b2, col_b3, col_b4 = st.columns(4)
        if not df_bakim.empty and "durum" in df_bakim.columns:
            toplam_plan = len(df_bakim)
            gecikmiş    = len(df_bakim[df_bakim["durum"] == "Gecikmiş"])
            bu_hafta    = 0
            try:
                df_bakim["_snr"] = pd.to_datetime(df_bakim["sonraki_bakim_tarihi"], format="%d/%m/%Y", errors="coerce").dt.date
                bu_hafta = len(df_bakim[(df_bakim["_snr"] >= date.today()) & (df_bakim["_snr"] <= date.today() + timedelta(days=7))])
                df_bakim = df_bakim.drop(columns=["_snr"])
            except:
                pass
            tamamlanan = len(df_bakim[df_bakim["durum"] == "Tamamlandı"])
        else:
            toplam_plan = gecikmiş = bu_hafta = tamamlanan = 0

        with col_b1: st.metric("📋 Toplam Plan", toplam_plan)
        with col_b2: st.metric("⚠️ Gecikmiş",    gecikmiş)
        with col_b3: st.metric("📅 Bu Hafta",     bu_hafta)
        with col_b4: st.metric("✅ Tamamlanan",   tamamlanan)

        if gecikmiş > 0:
            df_gec = df_bakim[df_bakim["durum"] == "Gecikmiş"]
            for _, row in df_gec.iterrows():
                st.markdown(f'<div class="kritik-banner">⚠️ <strong style="color:#fbbf24;">GECİKMİŞ BAKIM:</strong> <span style="color:#cbd5e1;"> {row.get("makine","")} — {row.get("bakim_turu","")}</span></div>', unsafe_allow_html=True)

        st.markdown("---")
        col_liste, col_form = st.columns([3, 2])

        with col_liste:
            st.markdown("#### 📋 Bakım Planı Listesi")
            col_fl1, col_fl2, col_fl3 = st.columns(3)
            with col_fl1: fl_bolge   = st.selectbox("Bölge",  ["Tümü"] + BOLGELER, key="bk_bolge")
            with col_fl2: fl_durum   = st.selectbox("Durum",  ["Tümü", "Bekliyor", "Gecikmiş", "Tamamlandı"], key="bk_durum")
            with col_fl3: fl_periyot = st.selectbox("Periyot", ["Tümü"] + list(PERIYOTLAR.keys()), key="bk_periyot")

            if not df_bakim.empty and "makine" in df_bakim.columns:
                gb = df_bakim.copy()
                if fl_bolge   != "Tümü": gb = gb[gb["bolge"]    == fl_bolge]
                if fl_durum   != "Tümü": gb = gb[gb["durum"]    == fl_durum]
                if fl_periyot != "Tümü":
                    gun = PERIYOTLAR[fl_periyot]
                    gb = gb[gb["periyot_gun"] == gun]

                if gb.empty:
                    st.info("Filtreye uyan bakım planı bulunamadı.")
                else:
                    gos_kol = [c for c in ["bolge", "makine", "bakim_turu", "sonraki_bakim_tarihi", "son_bakim_tarihi", "sorumlu", "durum"] if c in gb.columns]
                    gos_df  = gb[gos_kol].rename(columns={"bolge": "Bölge", "makine": "Makine", "bakim_turu": "Bakım Türü", "sonraki_bakim_tarihi": "Sonraki Bakım", "son_bakim_tarihi": "Son Bakım", "sorumlu": "Sorumlu", "durum": "Durum"})
                    st.dataframe(gos_df, use_container_width=True, hide_index=True)

                    st.markdown("#### ✅ Bakım Tamamlandı İşaretle")
                    bekleyen = df_bakim[df_bakim["durum"].isin(["Bekliyor", "Gecikmiş"])]
                    if not bekleyen.empty:
                        secenekler = bekleyen.apply(lambda r: f"[ID:{r['id']}] {r.get('bolge','')} | {r.get('makine','')} — {r.get('bakim_turu','')}", axis=1).tolist()
                        secilen_bakim = st.selectbox("Tamamlanan Bakım", secenekler, key="bakim_sec")
                        bakim_id      = int(secilen_bakim.split("ID:")[1].split("]")[0])
                        bakim_notu    = st.text_input("Bakım Notu (opsiyonel)", key="bakim_not")
                        if st.button("✅ Tamamlandı Olarak İşaretle", use_container_width=True, key="bakim_tamam"):
                            bakim_satir = df_bakim[df_bakim["id"] == bakim_id].iloc[0]
                            periyot_gun = int(bakim_satir.get("periyot_gun", 30))
                            bugun_fmt   = date.today().strftime("%d/%m/%Y")
                            sonraki_fmt = (date.today() + timedelta(days=periyot_gun)).strftime("%d/%m/%Y")
                            sb_update("bakim_plani", f"id=eq.{bakim_id}", {"durum": "Tamamlandı", "son_bakim_tarihi": bugun_fmt, "sonraki_bakim_tarihi": sonraki_fmt, "notlar": bakim_notu})
                            sb_insert("bakim_plani", {"bolge": bakim_satir.get("bolge", ""), "makine": bakim_satir.get("makine", ""), "bakim_turu": bakim_satir.get("bakim_turu", ""), "aciklama": bakim_satir.get("aciklama", ""), "periyot_gun": periyot_gun, "son_bakim_tarihi": bugun_fmt, "sonraki_bakim_tarihi": sonraki_fmt, "sorumlu": bakim_satir.get("sorumlu", ""), "durum": "Bekliyor", "notlar": ""})
                            bakim_df_getir.clear()
                            log_yaz("BAKIM TAMAMLANDI", f"ID:{bakim_id} — {bakim_satir.get('makine','')}")
                            st.success(f"✅ Bakım tamamlandı! Sonraki: **{sonraki_fmt}**")
                            time.sleep(1)
                            st.rerun()
                    else:
                        st.info("Bekleyen bakım bulunmuyor.")

                    st.download_button("📥 Bakım Planı İndir", gos_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), file_name=f"bakim_plani_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
            else:
                st.info("📭 Henüz bakım planı eklenmemiş.")

        with col_form:
            st.markdown("#### ➕ Yeni Bakım Planı Ekle")
            with st.form("bakim_ekle_formu"):
                bp_bolge    = st.selectbox("Bölge *", BOLGELER, key="bp_bolge")
                bp_makine   = st.selectbox("Makine *", aktif_makine_listesi().get(bp_bolge, MAKINE_LISTESI_BOLGE[bp_bolge]), key="bp_makine")
                bp_tur      = st.selectbox("Bakım Türü *", BAKIM_TURLERI, key="bp_tur")
                bp_periyot  = st.selectbox("Periyot *", list(PERIYOTLAR.keys()), key="bp_periyot")
                bp_aciklama = st.text_area("Açıklama", height=100, key="bp_aciklama")
                bp_sorumlu  = st.text_input("Sorumlu Teknisyen", key="bp_sorumlu", value=st.session_state.get("aktif_tam_ad", ""))
                bp_ilk_tar  = st.date_input("İlk Bakım Tarihi", value=date.today(), key="bp_tarih")
                submit_bakim = st.form_submit_button("📅 Bakım Planı Oluştur", use_container_width=True)
                if submit_bakim:
                    periyot_gun = PERIYOTLAR[bp_periyot]
                    son_tar     = bp_ilk_tar.strftime("%d/%m/%Y")
                    snr_tar     = (bp_ilk_tar + timedelta(days=periyot_gun)).strftime("%d/%m/%Y")
                    ok = sb_insert("bakim_plani", {"bolge": bp_bolge, "makine": bp_makine, "bakim_turu": bp_tur, "aciklama": bp_aciklama, "periyot_gun": periyot_gun, "son_bakim_tarihi": son_tar, "sonraki_bakim_tarihi": snr_tar, "sorumlu": bp_sorumlu, "durum": "Bekliyor", "notlar": ""})
                    if ok:
                        bakim_df_getir.clear()
                        log_yaz("BAKIM PLANI EKLENDİ", f"{bp_bolge} — {bp_makine} — {bp_tur}")
                        st.success(f"✅ Bakım planı oluşturuldu! Sonraki: **{snr_tar}**")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Kayıt başarısız.")

            if yetkili_mi("Yönetici") and not df_bakim.empty and "makine" in df_bakim.columns:
                st.markdown("---")
                st.markdown("#### 🗑️ Bakım Planı Sil")
                tum_planlar = df_bakim.apply(lambda r: f"[ID:{r['id']}] {r.get('bolge','')} | {r.get('makine','')} — {r.get('bakim_turu','')}", axis=1).tolist()
                sil_plan = st.selectbox("Silinecek Plan", tum_planlar, key="bakim_sil_sec")
                sil_id   = int(sil_plan.split("ID:")[1].split("]")[0])
                if st.button("🗑️ Planı Sil", key="bakim_sil_btn"):
                    sb_delete("bakim_plani", f"id=eq.{sil_id}")
                    bakim_df_getir.clear()
                    log_yaz("BAKIM PLANI SİLİNDİ", f"ID:{sil_id}")
                    st.success("Silindi.")
                    st.rerun()

        st.markdown("---")
        st.markdown("### ☑️ Checklist Yönetimi")
        if not df_bakim.empty and "makine" in df_bakim.columns:
            col_ck1, col_ck2 = st.columns([3, 2])
            with col_ck1:
                st.markdown("#### Mevcut Checklist Maddeleri")
                plan_sec_list = df_bakim.apply(lambda r: f"[ID:{r['id']}] {r.get('bolge','')} | {r.get('makine','')} — {r.get('bakim_turu','')}", axis=1).tolist()
                secilen_plan_str = st.selectbox("Bakım Planı Seçin", plan_sec_list, key="ck_plan_sec")
                secilen_plan_id  = int(secilen_plan_str.split("ID:")[1].split("]")[0])
                maddeler = checklist_getir(secilen_plan_id)
                if maddeler:
                    for m in maddeler:
                        col_m1, col_m2 = st.columns([5, 1])
                        with col_m1: st.markdown(f"**{m['sira']}.** {m['madde']}")
                        with col_m2:
                            if st.button("🗑️", key=f"madde_sil_{m['id']}"):
                                sb_update("bakim_checklist", f"id=eq.{m['id']}", {"aktif": False})
                                st.rerun()
                else:
                    st.info("Bu plan için henüz checklist maddesi eklenmemiş.")

            with col_ck2:
                st.markdown("#### ➕ Madde Ekle")
                with st.form("checklist_ekle"):
                    ck_madde = st.text_input("Kontrol Maddesi *", placeholder="Örn: Yağ seviyesi kontrol edildi")
                    ck_sira  = st.number_input("Sıra No", min_value=1, step=1, value=len(checklist_getir(secilen_plan_id)) + 1)
                    if st.form_submit_button("➕ Madde Ekle", use_container_width=True) and ck_madde.strip():
                        sb_insert("bakim_checklist", {"bakim_plani_id": secilen_plan_id, "sira": int(ck_sira), "madde": ck_madde.strip(), "aktif": True})
                        st.success(f"✅ '{ck_madde}' eklendi!")
                        time.sleep(0.5)
                        st.rerun()
                st.markdown("---")
                st.markdown("**📋 Toplu Madde Ekle**")
                with st.form("checklist_toplu"):
                    toplu_metin = st.text_area("Maddeler (her satır bir madde)", height=150)
                    if st.form_submit_button("📋 Hepsini Ekle", use_container_width=True) and toplu_metin.strip():
                        satirlar = [s.strip() for s in toplu_metin.strip().splitlines() if s.strip()]
                        mevcut_sira = len(checklist_getir(secilen_plan_id))
                        for i, satir in enumerate(satirlar):
                            sb_insert("bakim_checklist", {"bakim_plani_id": secilen_plan_id, "sira": mevcut_sira + i + 1, "madde": satir, "aktif": True})
                        st.success(f"✅ {len(satirlar)} madde eklendi!")
                        time.sleep(0.5)
                        st.rerun()
        else:
            st.info("Önce bakım planı oluşturun.")

        st.markdown("---")
        st.markdown("#### 📅 Takvim Görünümü — Önümüzdeki 30 Gün")
        if not df_bakim.empty and "sonraki_bakim_tarihi" in df_bakim.columns:
            try:
                df_takvim = df_bakim.copy()
                df_takvim["_snr"] = pd.to_datetime(df_takvim["sonraki_bakim_tarihi"], format="%d/%m/%Y", errors="coerce").dt.date
                df_takvim = df_takvim[(df_takvim["_snr"] >= date.today()) & (df_takvim["_snr"] <= date.today() + timedelta(days=30))].sort_values("_snr")
                if df_takvim.empty:
                    st.info("Önümüzdeki 30 günde planlanmış bakım bulunmuyor.")
                else:
                    for _, row in df_takvim.iterrows():
                        kalan = (row["_snr"] - date.today()).days
                        renk  = "#DC2626" if kalan <= 2 else "#D97706" if kalan <= 7 else "#16A34A"
                        st.markdown(f"""
                        <div class="durum-karti" style="margin-bottom:8px;">
                          <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div>
                              <span style="font-size:13px;font-weight:600;color:#e2e8f0;">{row.get("makine","")}</span>
                              <span style="font-size:12px;color:#64748b;margin-left:8px;">{row.get("bolge","")}</span><br>
                              <span style="font-size:12px;color:#94a3b8;">{row.get("bakim_turu","")} — {row.get("sorumlu","—")}</span>
                            </div>
                            <div style="text-align:right;">
                              <div style="font-size:14px;font-weight:700;color:{renk};">{row["sonraki_bakim_tarihi"]}</div>
                              <div style="font-size:11px;color:#64748b;">{kalan} gün sonra</div>
                            </div>
                          </div>
                        </div>""", unsafe_allow_html=True)
            except Exception as e:
                st.caption(f"Takvim yüklenemedi: {e}")


# =============================================================================
# SEKME 7: OEE ANALİZİ
# =============================================================================

@st.cache_data(ttl=30)
def oee_df_getir():
    try:
        rows = sb_select("oee_kayit")
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        df = df.drop(columns=[c for c in ["created_at"] if c in df.columns])
        return df
    except Exception:
        return pd.DataFrame()

def oee_renk(deger):
    if deger >= 85:   return "#16A34A"
    elif deger >= 65: return "#D97706"
    else:             return "#DC2626"

with tab_oee:
    if not giris_gerektir("Yönetici"):
        pass
    else:
        st.markdown("### 📈 OEE — Ekipman Etkinlik Analizi")
        st.caption("Mevcut arıza verilerinden otomatik hesaplanır. Hedef: Availability ≥ %90 | OEE ≥ %85")
        df_ariza_oee = ariza_df_getir()

        if df_ariza_oee.empty or "Durum" not in df_ariza_oee.columns:
            st.info("📭 Henüz yeterli arıza verisi yok.")
        else:
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1: oee_bolge = st.selectbox("Bölge", ["Tümü"] + BOLGELER, key="oee_bolge")
            with col_f2: oee_gun   = st.selectbox("Dönem", ["Son 7 Gün", "Son 30 Gün", "Son 90 Gün", "Tüm Zamanlar"], key="oee_gun")
            with col_f3: vardiya_suresi = st.number_input("Vardiya Süresi (dk)", min_value=60, max_value=1440, step=60, value=480)

            gun_map = {"Son 7 Gün": 7, "Son 30 Gün": 30, "Son 90 Gün": 90, "Tüm Zamanlar": 3650}
            bas_tarih_oee = date.today() - timedelta(days=gun_map[oee_gun])
            df_o = df_ariza_oee.copy()
            if oee_bolge != "Tümü" and "Bölge" in df_o.columns:
                df_o = df_o[df_o["Bölge"] == oee_bolge]
            try:
                df_o["_ac"] = pd.to_datetime(df_o["Açılış Tarihi"], format="%d/%m/%Y %H:%M", errors="coerce").dt.date
                df_o = df_o[df_o["_ac"] >= bas_tarih_oee]
            except:
                pass

            if df_o.empty:
                st.info("Seçilen dönemde veri bulunamadı.")
            else:
                df_kapali = df_o[df_o["Durum"] == "Kapalı"].copy()
                df_kapali["sure"] = pd.to_numeric(df_kapali.get("Çözüm Süresi (Dk)", pd.Series()), errors="coerce").fillna(0)

                ozet = []
                for makine, grp in df_kapali.groupby("Makine"):
                    toplam_ariza   = len(grp)
                    toplam_durakma = grp["sure"].sum()
                    gun_sayisi     = max((date.today() - bas_tarih_oee).days, 1)
                    toplam_plan    = gun_sayisi * vardiya_suresi
                    availability   = round(max(0, (toplam_plan - toplam_durakma) / toplam_plan * 100), 1)
                    mttr = round(grp["sure"].mean(), 1) if toplam_ariza > 0 else 0
                    mtbf_dk = None
                    if toplam_ariza >= 2 and "Kapatma Tarihi" in grp.columns:
                        grp2 = grp.copy()
                        grp2["kap"] = pd.to_datetime(grp2["Kapatma Tarihi"], format="%d/%m/%Y %H:%M", errors="coerce")
                        grp2 = grp2.dropna(subset=["kap"]).sort_values("kap")
                        if len(grp2) >= 2:
                            fark = grp2["kap"].diff().dropna()
                            mtbf_dk = round(fark.dt.total_seconds().mean() / 60, 1)
                    durum = "🟢 İyi" if availability >= 90 else "🟡 Geliştirilmeli" if availability >= 70 else "🔴 Kritik"
                    ozet.append({"Makine": makine, "Arıza Sayısı": toplam_ariza, "Toplam Durakma (dk)": int(toplam_durakma), "MTTR (dk)": mttr, "MTBF (dk)": mtbf_dk if mtbf_dk else "—", "Availability (%)": min(availability, 100), "OEE* (%)": min(availability, 100), "Durum": durum})

                if not ozet:
                    st.info("Kapatılmış arıza verisi bulunamadı.")
                else:
                    df_ozet = pd.DataFrame(ozet).sort_values("Availability (%)", ascending=False)
                    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
                    ort_avail = round(df_ozet["Availability (%)"].mean(), 1)
                    ort_mttr  = round(df_kapali["sure"].mean(), 1) if not df_kapali.empty else 0
                    with col_k1:
                        renk_a = oee_renk(ort_avail)
                        st.markdown(f'<div style="background:rgba(30,41,59,0.8);border:1px solid {renk_a}44;border-radius:12px;padding:16px 20px;"><div style="font-size:11px;color:#94a3b8;font-weight:600;text-transform:uppercase;">ORT. AVAİLABİLİTY</div><div style="font-size:32px;font-weight:800;color:{renk_a};margin-top:4px;">%{ort_avail}</div><div style="font-size:11px;color:#64748b;">Hedef: ≥%90</div></div>', unsafe_allow_html=True)
                    with col_k2: st.metric("⏱ Ort. MTTR", f"{ort_mttr} dk")
                    with col_k3: st.metric("🟢 En İyi", df_ozet.iloc[0]["Makine"], delta=f"%{df_ozet.iloc[0]['Availability (%)']}")
                    with col_k4: st.metric("🔴 Geliştirilmeli", df_ozet.iloc[-1]["Makine"], delta=f"%{df_ozet.iloc[-1]['Availability (%)']}")
                    st.markdown("---")
                    st.markdown("#### 📋 Makine Bazlı Availability Tablosu")
                    st.caption("*OEE = Availability (Performance ve Quality için üretim verisi gerekir)")
                    st.dataframe(df_ozet, use_container_width=True, hide_index=True)
                    st.markdown("#### 📊 Availability Karşılaştırması")
                    st.bar_chart(df_ozet.set_index("Makine")["Availability (%)"], height=260)
                    st.markdown("---")
                    st.markdown("#### 💡 Öneri & Aksiyon")
                    for _, row in df_ozet.iterrows():
                        av = row["Availability (%)"]
                        if av < 70:
                            st.markdown(f'<div class="kritik-banner">🚨 <strong style="color:#f87171;">{row["Makine"]}</strong> — Availability %{av} → Acil bakım/revizyon planı yapın.</div>', unsafe_allow_html=True)
                        elif av < 90:
                            st.warning(f"⚠️ **{row['Makine']}** — Availability %{av} → Periyodik bakım sıklığını artırın.")
                    st.download_button("📥 OEE Raporu İndir", df_ozet.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), file_name=f"oee_raporu_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

# =============================================================================
# SEKME 8: AI TAHMİN
# =============================================================================

with tab_ai:
    if not giris_gerektir("Yönetici"):
        pass
    else:
        st.markdown("### 🤖 AI Arıza Tahmin & Analiz Motoru")
        df_ai = ariza_df_getir()

        if df_ai.empty or len(df_ai) < 5:
            st.warning("⚠️ AI analizi için en az 5 kapatılmış arıza kaydı gerekli.")
        else:
            try:
                api_key = ""
                try: api_key = st.secrets["anthropic_api_key"]
                except: pass
                if not api_key:
                    try: api_key = st.secrets["email"]["anthropic_api_key"]
                    except: pass
                if not api_key or not api_key.startswith("sk-"):
                    raise KeyError("API key bulunamadı")
                st.success("✅ Claude API bağlantısı hazır.")
            except KeyError:
                st.error("❌ Anthropic API key bulunamadı. Streamlit Secrets'a `anthropic_api_key` ekleyin.")
                st.stop()

            col_ai1, col_ai2 = st.columns([2, 1])
            with col_ai2:
                st.markdown("#### ⚙️ Analiz Ayarları")
                ai_bolge = st.selectbox("Bölge", ["Tümü"] + BOLGELER, key="ai_bolge")
                ai_gun   = st.selectbox("Dönem", ["Son 30 Gün", "Son 90 Gün", "Tüm Zamanlar"], key="ai_gun")
                ai_tip   = st.selectbox("Analiz Tipi", ["🔮 Makine Risk Analizi", "📊 Arıza Trend Analizi", "👨‍🔧 Teknisyen Performans Değerlendirmesi", "💡 Bakım Optimizasyon Önerileri", "🎯 Genel Sistem Sağlık Raporu"], key="ai_tip")
                analiz_btn = st.button("🚀 AI Analizi Başlat", use_container_width=True, key="ai_btn")

            with col_ai1:
                st.markdown("#### 📋 Analiz Kapsamı")
                gun_map = {"Son 30 Gün": 30, "Son 90 Gün": 90, "Tüm Zamanlar": 3650}
                df_fil = df_ai.copy()
                if ai_bolge != "Tümü" and "Bölge" in df_fil.columns:
                    df_fil = df_fil[df_fil["Bölge"] == ai_bolge]
                try:
                    df_fil["_t"] = pd.to_datetime(df_fil["Açılış Tarihi"], format="%d/%m/%Y %H:%M", errors="coerce").dt.date
                    df_fil = df_fil[df_fil["_t"] >= date.today() - timedelta(days=gun_map[ai_gun])]
                except:
                    pass
                df_kap_ai = df_fil[df_fil["Durum"] == "Kapalı"].copy()
                df_kap_ai["sure"] = pd.to_numeric(df_kap_ai.get("Çözüm Süresi (Dk)", pd.Series(dtype=float)), errors="coerce").fillna(0)
                col_s1, col_s2, col_s3 = st.columns(3)
                with col_s1: st.metric("📋 Toplam Kayıt", len(df_fil))
                with col_s2: st.metric("✅ Kapatılmış", len(df_kap_ai))
                with col_s3: st.metric("🏭 Farklı Makine", df_fil["Makine"].nunique() if "Makine" in df_fil.columns else 0)
                if "ai_sonuc" not in st.session_state: st.session_state["ai_sonuc"] = ""
                if "ai_tip_sonuc" not in st.session_state: st.session_state["ai_tip_sonuc"] = ""

            if analiz_btn:
                if len(df_kap_ai) < 3:
                    st.warning("⚠️ Seçilen dönemde yeterli kapatılmış arıza yok.")
                else:
                    mak_ozet = df_kap_ai.groupby("Makine").agg(ariza_sayi=("Makine","count"), ort_sure=("sure","mean"), toplam_sure=("sure","sum")).round(1).reset_index()
                    tur_ozet = df_kap_ai["Arıza Türü"].value_counts().head(5).to_dict() if "Arıza Türü" in df_kap_ai.columns else {}
                    tek_ozet = df_kap_ai["Müdahale Eden"].value_counts().head(5).to_dict() if "Müdahale Eden" in df_kap_ai.columns else {}
                    sla_asan = len(df_kap_ai[df_kap_ai["SLA Durumu"].str.contains("Aşıldı", na=False)]) if "SLA Durumu" in df_kap_ai.columns else 0
                    tip_prompt = {
                        "🔮 Makine Risk Analizi": "Her makine için arıza risk seviyesini (Düşük/Orta/Yüksek/Kritik) belirle. En riskli 3 makineyi öncelikli öner.",
                        "📊 Arıza Trend Analizi": "Arıza trendlerini analiz et. Hangi arıza türleri artıyor? Gelecek 30 günde hangi sorunlar beklenmeli?",
                        "👨‍🔧 Teknisyen Performans Değerlendirmesi": "Teknisyen verilerini analiz et. Kim en verimli? İş yükü dengeli mi?",
                        "💡 Bakım Optimizasyon Önerileri": "Bakım stratejisini değerlendir. Hangi makinelere periyodik bakım eklenmeli?",
                        "🎯 Genel Sistem Sağlık Raporu": "Tesisin genel bakım sağlığını değerlendir. Güçlü/zayıf yanlar ve öneriler."
                    }
                    prompt = f"""Sen endüstriyel bakım yönetimi uzmanısın. Türkçe yanıt ver.
Bölge: {ai_bolge} | Dönem: {ai_gun} | Kapatılmış Arıza: {len(df_kap_ai)} | SLA Aşımı: {sla_asan}

Makine Özeti:\n{mak_ozet.to_string(index=False)}

Arıza Türleri:\n{chr(10).join([f"- {k}: {v}" for k,v in tur_ozet.items()])}

Görevin: {tip_prompt.get(ai_tip, "Genel analiz yap.")}

Format: 1)Özet 2)Kritik Bulgular 3)Acil Aksiyonlar 4)Uzun Vadeli Öneriler 5)Risk Skoru (0-100)"""
                    with st.spinner("🤖 Claude AI analiz yapıyor..."):
                        try:
                            resp = requests.post("https://api.anthropic.com/v1/messages", headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}, json={"model": "claude-haiku-4-5-20251001", "max_tokens": 1500, "messages": [{"role": "user", "content": prompt}]}, timeout=30)
                            if resp.ok:
                                sonuc = resp.json()["content"][0]["text"]
                                st.session_state["ai_sonuc"] = sonuc
                                st.session_state["ai_tip_sonuc"] = ai_tip
                                log_yaz("AI ANALİZ", f"{ai_tip} — {ai_bolge}")
                            else:
                                st.error(f"❌ API Hatası {resp.status_code}")
                        except Exception as e:
                            st.error(f"❌ Bağlantı hatası: {e}")

            if st.session_state.get("ai_sonuc"):
                st.markdown("---")
                st.markdown(f'<div style="background:rgba(61,0,102,0.6);border:1px solid rgba(255,215,0,0.2);border-left:4px solid #FFD700;border-radius:10px;padding:16px;margin-bottom:16px;"><div style="font-size:11px;color:#9B6FBF;font-weight:700;text-transform:uppercase;margin-bottom:8px;">🤖 Claude AI — {st.session_state.get("ai_tip_sonuc","")}</div></div>', unsafe_allow_html=True)
                st.markdown(st.session_state["ai_sonuc"])
                col_dl, col_yeni = st.columns([1, 3])
                with col_dl:
                    st.download_button("📥 Raporu İndir", data=st.session_state["ai_sonuc"].encode("utf-8"), file_name=f"ai_rapor_{datetime.now().strftime('%Y%m%d_%H%M')}.txt", mime="text/plain")
                with col_yeni:
                    if st.button("🔄 Yeni Analiz", key="ai_temizle"):
                        st.session_state["ai_sonuc"] = ""
                        st.rerun()
            elif not analiz_btn:
                st.markdown('<div style="text-align:center;padding:40px;background:rgba(61,0,102,0.4);border:1px solid rgba(255,215,0,0.1);border-radius:12px;"><div style="font-size:48px;margin-bottom:12px;">🤖</div><div style="font-size:16px;font-weight:700;color:#FFD700;margin-bottom:8px;">AI Analizi Hazır</div><div style="font-size:13px;color:#9B6FBF;">Sağdaki seçeneklerden analiz tipini seçin ve başlatın.</div></div>', unsafe_allow_html=True)


# =============================================================================
# SEKME 9: DİJİTAL İKİZ
# =============================================================================

with tab_twin:
    if not giris_gerektir("Teknisyen"):
        pass
    else:
        st.markdown("### 🏭 Dijital İkiz — Tesis Makine Durumu")
        df_twin = ariza_df_getir()
        twin_bolge = st.radio("Tesis", ["🏭 Adana LM", "🏭 Tuzla LM"], horizontal=True, key="twin_bolge")
        bolge_kisa = "Adana" if "Adana" in twin_bolge else "Tuzla"

        bolge_df = pd.DataFrame()
        if not df_twin.empty and "Bölge" in df_twin.columns:
            bolge_df = df_twin[df_twin["Bölge"].str.contains(bolge_kisa, na=False)]

        mak_listesi_db = aktif_makine_listesi()
        gercek_makineler = []
        for k, v in mak_listesi_db.items():
            if bolge_kisa in k:
                gercek_makineler = [m for m in v if m and m != "Diğer"]
                break
        if not gercek_makineler and not bolge_df.empty and "Makine" in bolge_df.columns:
            gercek_makineler = sorted([m for m in bolge_df["Makine"].unique() if m and m != "Diğer"])

        def makine_durum(mak, df):
            if df.empty or "Makine" not in df.columns: return "bilgi-yok", "", 0
            mdf = df[df["Makine"] == mak]
            if mdf.empty: return "bilgi-yok", "", 0
            kritik = mdf[(mdf["Durum"]=="Açık") & (mdf["Öncelik"].str.startswith("🔴",na=False))]
            if not kritik.empty: return "kritik", str(kritik.iloc[0].get("Arıza Tanımı",""))[:40], len(kritik)
            acik = mdf[mdf["Durum"]=="Açık"]
            if not acik.empty: return "uyari", str(acik.iloc[0].get("Arıza Tanımı",""))[:40], len(acik)
            return "normal", "Çalışıyor", 0

        def grup_belirle(mak):
            m = mak.upper()
            if any(x in m for x in ["VNA","VNA-"]): return "🚜 VNA Araçlar"
            if any(x in m for x in ["RT-","REACH"]): return "🔄 Reach Truck"
            if any(x in m for x in ["KONVEYÖR","KONVEYOR","BANT"]): return "📦 Konveyör"
            if any(x in m for x in ["ELEKTRİK","ELEKTRIK","PANO","KOMPRESÖR","SOĞUTMA","JENERATÖR","MCC"]): return "⚡ Elektrik & Enerji"
            if any(x in m for x in ["FORKLİFT","FORKLIFT","FLT","TRANSPALET"]): return "🚛 Taşıma & Lojistik"
            if any(x in m for x in ["ŞARJ","SARJ","KAPI","YANGIN"]): return "🔧 Altyapı"
            return "📋 Diğer"

        durum_cfg = {
            "kritik":    {"renk":"#993556","bg":"#FBEAF0","border":"#D4537E","ikon":"🔴","etiket":"KRİTİK"},
            "uyari":     {"renk":"#854F0B","bg":"#FAEEDA","border":"#BA7517","ikon":"🟡","etiket":"AÇIK TALEP"},
            "normal":    {"renk":"#3B6D11","bg":"#EAF3DE","border":"#639922","ikon":"🟢","etiket":"NORMAL"},
            "bilgi-yok": {"renk":"#5F5E5A","bg":"#F1EFE8","border":"#B4B2A9","ikon":"⚫","etiket":"VERİ YOK"},
        }

        toplam_mak = len(gercek_makineler)
        kritik_mak = sum(1 for m in gercek_makineler if makine_durum(m, bolge_df)[0]=="kritik")
        uyari_mak  = sum(1 for m in gercek_makineler if makine_durum(m, bolge_df)[0]=="uyari")
        normal_mak = sum(1 for m in gercek_makineler if makine_durum(m, bolge_df)[0]=="normal")

        st.markdown(f"""
        <div style="display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin-bottom:20px;">
          <div style="background:rgba(61,0,102,0.8);border:0.5px solid rgba(255,215,0,0.2);border-radius:10px;padding:12px;text-align:center;"><div style="font-size:10px;color:#9B6FBF;text-transform:uppercase;margin-bottom:4px;">Toplam Makine</div><div style="font-size:26px;font-weight:700;color:#FFD700;">{toplam_mak}</div></div>
          <div style="background:rgba(74,222,128,0.08);border:0.5px solid #639922;border-radius:10px;padding:12px;text-align:center;"><div style="font-size:10px;color:#5F5E5A;text-transform:uppercase;margin-bottom:4px;">Normal</div><div style="font-size:26px;font-weight:700;color:#3B6D11;">{normal_mak}</div></div>
          <div style="background:rgba(239,159,39,0.08);border:0.5px solid #BA7517;border-radius:10px;padding:12px;text-align:center;"><div style="font-size:10px;color:#5F5E5A;text-transform:uppercase;margin-bottom:4px;">Açık Talep</div><div style="font-size:26px;font-weight:700;color:#854F0B;">{uyari_mak}</div></div>
          <div style="background:rgba(212,83,126,0.08);border:0.5px solid #D4537E;border-radius:10px;padding:12px;text-align:center;"><div style="font-size:10px;color:#5F5E5A;text-transform:uppercase;margin-bottom:4px;">Kritik</div><div style="font-size:26px;font-weight:700;color:#993556;">{kritik_mak}</div></div>
        </div>""", unsafe_allow_html=True)

        if not gercek_makineler:
            st.info("Makine bulunamadı. Sistem Ayarları'ndan ekleyin.")
        else:
            dinamik_gruplar = {}
            for mak in gercek_makineler:
                grup = grup_belirle(mak)
                dinamik_gruplar.setdefault(grup, []).append(mak)

            for grup_adi, makineler in dinamik_gruplar.items():
                st.markdown(f"**{grup_adi}**")
                cols_per_row = 5
                rows = [makineler[i:i+cols_per_row] for i in range(0, len(makineler), cols_per_row)]
                for satir in rows:
                    cols = st.columns(len(satir))
                    for col, mak in zip(cols, satir):
                        with col:
                            durum, aciklama, sayi = makine_durum(mak, bolge_df)
                            cfg = durum_cfg[durum]
                            mak_kisa = mak
                            for suf in [" (Hat A)"," (Hat B)"," (Tuzla)"," (Tuzla Depo)"," (Depo Sahası)"," (Adana LM)"," (Tuzla LM)"]:
                                mak_kisa = mak_kisa.replace(suf,"")
                            h  = f'<div style="background:{cfg["bg"]};border:1.5px solid {cfg["border"]};border-radius:10px;padding:12px 8px;text-align:center;min-height:90px;">'
                            h += f'<div style="font-size:20px;margin-bottom:4px;">{cfg["ikon"]}</div>'
                            h += f'<div style="font-size:11px;font-weight:600;color:#2C2C2A;line-height:1.3;margin-bottom:3px;">{mak_kisa}</div>'
                            h += f'<div style="font-size:10px;font-weight:700;color:{cfg["renk"]};text-transform:uppercase;">{cfg["etiket"]}</div>'
                            if sayi > 0: h += f'<div style="font-size:9px;color:#5F5E5A;margin-top:2px;">{sayi} talep</div>'
                            h += '</div>'
                            st.markdown(h, unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### Makine Detayı")
            sec_mak = st.selectbox("Makine seç", gercek_makineler, key="twin_detay")
            if sec_mak:
                durum_d, aciklama_d, sayi_d = makine_durum(sec_mak, bolge_df)
                cfg_d = durum_cfg[durum_d]
                mak_df_d = bolge_df[bolge_df["Makine"]==sec_mak] if not bolge_df.empty and "Makine" in bolge_df.columns else pd.DataFrame()
                col1, col2 = st.columns([1, 2])
                with col1:
                    dh = f'<div style="background:{cfg_d["bg"]};border:2px solid {cfg_d["border"]};border-radius:12px;padding:20px;text-align:center;"><div style="font-size:36px;">{cfg_d["ikon"]}</div><div style="font-size:14px;font-weight:600;color:#2C2C2A;margin:8px 0 4px;">{sec_mak}</div><div style="font-size:12px;font-weight:700;color:{cfg_d["renk"]};text-transform:uppercase;">{cfg_d["etiket"]}</div>'
                    if aciklama_d: dh += f'<div style="font-size:11px;color:#5F5E5A;margin-top:6px;">{aciklama_d}</div>'
                    dh += '</div>'
                    st.markdown(dh, unsafe_allow_html=True)
                with col2:
                    if not mak_df_d.empty:
                        df_kap_d = mak_df_d[mak_df_d["Durum"]=="Kapalı"].copy()
                        df_kap_d["sure"] = pd.to_numeric(df_kap_d.get("Çözüm Süresi (Dk)", pd.Series(dtype=float)), errors="coerce").fillna(0)
                        c1, c2, c3 = st.columns(3)
                        with c1: st.metric("Toplam Arıza", len(mak_df_d))
                        with c2: st.metric("Kapatılan", len(df_kap_d))
                        with c3: st.metric("MTTR", f"{round(df_kap_d['sure'].mean(),1) if not df_kap_d.empty else 0} dk")
                        gs = [s for s in ["Talep No","Açılış Tarihi","Öncelik","Durum","SLA Durumu"] if s in mak_df_d.columns]
                        st.dataframe(mak_df_d[gs].head(5), use_container_width=True, hide_index=True)
                    else:
                        st.info("Bu makine için henüz arıza kaydı bulunmuyor.")

# =============================================================================
# SEKME 10: SİSTEM AYARLARI
# =============================================================================

with tab_ayar:
    if not giris_gerektir("Yönetici"):
        pass
    else:
        st.markdown("### ⚙️ Sistem Ayarları & Kullanıcı Yönetimi")
        col_a1, col_a2 = st.columns(2)

        with col_a1:
            st.markdown("#### 👥 Kullanıcı Listesi")
            kullanicilar = kullanicilari_yukle()
            for k_ad, k_bilgi in kullanicilar.items():
                st.markdown(f'<div class="durum-karti" style="padding:12px 16px;margin-bottom:8px;"><span style="font-weight:600;color:#e2e8f0;">{k_bilgi["tam_ad"]}</span><span style="font-size:12px;color:#64748b;margin-left:8px;">@{k_ad}</span><span class="sla-badge sla-ok" style="margin-left:8px;">{k_bilgi["rol"]}</span></div>', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### ✏️ Kullanıcı Düzenle")
            with st.form("kullanici_duzenle"):
                duz_sec = st.selectbox("Düzenlenecek", list(kullanicilar.keys()), format_func=lambda k: f"{kullanicilar[k]['tam_ad']} (@{k})")
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    duz_ad  = st.text_input("Ad Soyad", value=kullanicilar[duz_sec]["tam_ad"])
                    duz_rol = st.selectbox("Rol", ["Operatör","Teknisyen","Yönetici"], index=["Operatör","Teknisyen","Yönetici"].index(kullanicilar[duz_sec]["rol"]))
                with col_d2:
                    duz_s1 = st.text_input("Yeni Şifre", type="password", placeholder="••••••")
                    duz_s2 = st.text_input("Şifre Tekrar", type="password", placeholder="••••••")
                if st.form_submit_button("💾 Kaydet", use_container_width=True):
                    if duz_s1 and duz_s1 != duz_s2:
                        st.error("❌ Şifreler eşleşmiyor!")
                    else:
                        gv = {"tam_ad": duz_ad.strip() or kullanicilar[duz_sec]["tam_ad"], "rol": duz_rol}
                        if duz_s1: gv["sifre_hash"] = sifre_hashle(duz_s1)
                        sb_update("kullanicilar", f"kullanici_adi=eq.{duz_sec}", gv)
                        cache_temizle()
                        log_yaz("KULLANICI GÜNCELLENDİ", f"{duz_sec}→{duz_rol}")
                        st.success(f"✅ {duz_sec} güncellendi!")
                        st.rerun()

            st.markdown("---")
            st.markdown("#### ➕ Yeni Kullanıcı Ekle")
            with st.form("yeni_kullanici"):
                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    y_kul  = st.text_input("Kullanıcı Adı")
                    y_sif  = st.text_input("Şifre", type="password")
                with col_u2:
                    y_ad2  = st.text_input("Ad Soyad")
                    y_rol2 = st.selectbox("Rol", ["Operatör","Teknisyen","Yönetici"])
                if st.form_submit_button("Kullanıcı Oluştur", use_container_width=True):
                    if not all([y_kul, y_sif, y_ad2]): st.error("Tüm alanlar zorunludur.")
                    elif y_kul.lower() in kullanicilar: st.error("Bu kullanıcı adı zaten mevcut.")
                    else:
                        sb_insert("kullanicilar", {"kullanici_adi": y_kul.lower(), "sifre_hash": sifre_hashle(y_sif), "rol": y_rol2, "tam_ad": y_ad2})
                        cache_temizle()
                        log_yaz("KULLANICI OLUŞTURULDU", f"{y_kul} — {y_rol2}")
                        st.success(f"✅ {y_ad2} ({y_rol2}) oluşturuldu!")
                        st.rerun()

        with col_a2:
            st.markdown("#### 🏭 Makine Listesi Yönetimi")
            with st.expander("Makine Ekle / Sil", expanded=False):
                mk_rows = sb_select("makine_listesi", "aktif=eq.true")
                if mk_rows:
                    df_mk = pd.DataFrame(mk_rows)[["bolge","makine_adi"]]
                    df_mk.columns = ["Bölge","Makine Adı"]
                    st.dataframe(df_mk, use_container_width=True, hide_index=True)
                else:
                    st.caption("Henüz eklenmemiş — sabit liste kullanılıyor.")
                with st.form("makine_ekle"):
                    m_bolge = st.selectbox("Bölge", BOLGELER, key="mb")
                    m_ad    = st.text_input("Makine Adı", placeholder="Örn: VNA-05 (Hat C)")
                    if st.form_submit_button("➕ Ekle", use_container_width=True) and m_ad.strip():
                        sb_insert("makine_listesi", {"bolge": m_bolge, "makine_adi": m_ad.strip(), "aktif": True})
                        cache_temizle()
                        log_yaz("MAKİNE EKLENDİ", f"{m_bolge} — {m_ad}")
                        st.success(f"✅ {m_ad} eklendi!")
                        st.rerun()

            st.markdown("---")
            st.markdown("#### 📜 Sistem Aktivite Logu")
            try:
                log_rows = sb_select("sistem_log")
                if log_rows:
                    df_log = pd.DataFrame(log_rows).rename(columns={"zaman":"Zaman","kullanici":"Kullanıcı","islem":"İşlem","detay":"Detay"})
                    st.dataframe(df_log.sort_values("Zaman", ascending=False).head(50), use_container_width=True, hide_index=True)
                    st.download_button("📥 Log İndir", df_log.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), file_name=f"log_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
                else:
                    st.info("Henüz log kaydı yok.")
            except Exception as e:
                st.info(f"Log yüklenemedi: {e}")

            st.markdown("---")
            st.markdown("#### 📧 Email Alıcı Yönetimi")
            st.caption("Hangi bildirim türünü kimin alacağını buradan yönetebilirsiniz.")

            alici_rows = sb_select("email_alicilar")
            if alici_rows:
                df_alici = pd.DataFrame(alici_rows)
                gosterim_kol = ["ad", "email", "kritik_ariza", "haftalik_rapor", "stok_uyari", "talep_kapatma", "aktif"]
                gosterim_kol = [c for c in gosterim_kol if c in df_alici.columns]
                df_goster = df_alici[gosterim_kol].rename(columns={
                    "ad": "Ad", "email": "E-posta", "kritik_ariza": "Kritik Arıza",
                    "haftalik_rapor": "Haftalık Rapor", "stok_uyari": "Stok Uyarısı",
                    "talep_kapatma": "Talep Kapatma", "aktif": "Aktif"
                })
                st.dataframe(df_goster, use_container_width=True, hide_index=True)
            else:
                st.caption("Henüz alıcı tanımlanmamış — secrets.toml'daki sabit liste kullanılıyor.")

            with st.expander("✏️ Alıcı Ekle / Düzenle"):
                duzenleme_modu = st.radio("İşlem", ["➕ Yeni Alıcı Ekle", "✏️ Mevcut Alıcıyı Düzenle"], horizontal=True, key="alici_islem")

                if duzenleme_modu == "➕ Yeni Alıcı Ekle":
                    with st.form("yeni_alici_formu", clear_on_submit=True):
                        ya_ad    = st.text_input("Ad Soyad")
                        ya_email = st.text_input("E-posta *")
                        col_ya1, col_ya2 = st.columns(2)
                        with col_ya1:
                            ya_kritik   = st.checkbox("🚨 Kritik/Yüksek Arıza Bildirimleri", value=True)
                            ya_haftalik = st.checkbox("📊 Haftalık Rapor", value=True)
                        with col_ya2:
                            ya_stok    = st.checkbox("📦 Kritik Stok Uyarısı", value=True)
                            ya_kapatma = st.checkbox("✅ Talep Kapatma Bildirimi", value=False)
                        if st.form_submit_button("✅ Alıcı Ekle", use_container_width=True):
                            if not ya_email.strip():
                                st.error("❌ E-posta zorunludur.")
                            else:
                                sb_insert("email_alicilar", {
                                    "ad": ya_ad.strip(), "email": ya_email.strip(),
                                    "aktif": True, "kritik_ariza": ya_kritik,
                                    "haftalik_rapor": ya_haftalik, "stok_uyari": ya_stok,
                                    "talep_kapatma": ya_kapatma
                                })
                                log_yaz("EMAIL ALICI EKLENDİ", ya_email.strip())
                                st.success(f"✅ {ya_email} eklendi!")
                                time.sleep(0.8)
                                st.rerun()
                else:
                    if not alici_rows:
                        st.info("Düzenlenecek alıcı bulunmuyor. Önce bir alıcı ekleyin.")
                    else:
                        secim_str = [f"[ID:{r['id']}] {r.get('ad','')} — {r.get('email','')}" for r in alici_rows]
                        secilen_str = st.selectbox("Düzenlenecek Alıcı", secim_str, key="alici_duzenle_sec")
                        secilen_id = int(secilen_str.split("ID:")[1].split("]")[0])
                        secilen_row = next(r for r in alici_rows if r["id"] == secilen_id)
                        with st.form(f"alici_duzenle_formu_{secilen_id}"):
                            da_ad    = st.text_input("Ad Soyad", value=secilen_row.get("ad", "") or "", key=f"da_ad_{secilen_id}")
                            da_email = st.text_input("E-posta", value=secilen_row.get("email", "") or "", key=f"da_email_{secilen_id}")
                            col_da1, col_da2 = st.columns(2)
                            with col_da1:
                                da_kritik   = st.checkbox("🚨 Kritik/Yüksek Arıza", value=bool(secilen_row.get("kritik_ariza", True)), key=f"da_kritik_{secilen_id}")
                                da_haftalik = st.checkbox("📊 Haftalık Rapor", value=bool(secilen_row.get("haftalik_rapor", True)), key=f"da_haftalik_{secilen_id}")
                            with col_da2:
                                da_stok     = st.checkbox("📦 Kritik Stok Uyarısı", value=bool(secilen_row.get("stok_uyari", True)), key=f"da_stok_{secilen_id}")
                                da_kapatma  = st.checkbox("✅ Talep Kapatma", value=bool(secilen_row.get("talep_kapatma", False)), key=f"da_kapatma_{secilen_id}")
                            da_aktif = st.checkbox("Aktif", value=bool(secilen_row.get("aktif", True)), key=f"da_aktif_{secilen_id}")
                            col_kaydet, col_sil = st.columns(2)
                            with col_kaydet:
                                guncelle_btn = st.form_submit_button("💾 Güncelle", use_container_width=True)
                            with col_sil:
                                sil_btn = st.form_submit_button("🗑️ Sil", use_container_width=True)

                            if guncelle_btn:
                                if not da_email.strip():
                                    st.error("❌ E-posta boş olamaz.")
                                else:
                                    guncelleme_ok = sb_update("email_alicilar", f"id=eq.{secilen_id}", {
                                        "ad": da_ad.strip(), "email": da_email.strip(),
                                        "kritik_ariza": da_kritik, "haftalik_rapor": da_haftalik,
                                        "stok_uyari": da_stok, "talep_kapatma": da_kapatma,
                                        "aktif": da_aktif
                                    })
                                    if guncelleme_ok:
                                        log_yaz("EMAIL ALICI GÜNCELLENDİ", da_email.strip())
                                        st.success("✅ Güncellendi!")
                                        time.sleep(0.8)
                                        st.rerun()
                                    else:
                                        st.error("❌ Güncelleme başarısız oldu. Supabase bağlantısını kontrol edin.")
                            if sil_btn:
                                sb_delete("email_alicilar", f"id=eq.{secilen_id}")
                                log_yaz("EMAIL ALICI SİLİNDİ", secilen_row.get("email", ""))
                                st.success("Silindi.")
                                time.sleep(0.8)
                                st.rerun()

            st.markdown("---")
            st.markdown("#### 📊 Haftalık Rapor & Email Ayarları")
            try:
                rapor_log = sb_select("haftalik_rapor_log")
                if rapor_log:
                    son = rapor_log[0]
                    st.success(f"✅ Son rapor: **{son.get('gonderim_tarihi','')}** — {son.get('durum','')}")
            except:
                pass

            if st.button("📧 Anlık Durum Raporu Gönder", use_container_width=True):
                with st.spinner("Rapor hazırlanıyor..."):
                    try:
                        df_test = ariza_df_getir()
                        acik_t   = len(df_test[df_test["Durum"]=="Açık"]) if not df_test.empty and "Durum" in df_test.columns else 0
                        kritik_t = len(df_test[(df_test["Durum"]=="Açık") & (df_test["Öncelik"].str.startswith("🔴",na=False))]) if not df_test.empty else 0
                        ok = email_gonder("[TEST] Anlık Bakım Raporu", f"Toplam: {len(df_test)} | Açık: {acik_t} | Kritik: {kritik_t}")
                        if ok: st.success("✅ Rapor gönderildi!")
                        else:  st.error("❌ Email gönderilemedi. Ayarları kontrol edin.")
                    except Exception as e:
                        st.error(f"❌ Hata: {e}")

            try:
                gonderici = st.secrets["email"]["gonderici"]
                alici     = st.secrets["email"]["alici"]
                st.success(f"✅ Email: **{gonderici}** → **{alici}**")
            except KeyError:
                st.warning("⚠️ Email henüz yapılandırılmamış.")

            st.markdown("---")
            st.markdown("#### 🗄️ Veri Yedekleme")
            col_bk1, col_bk2 = st.columns(2)
            with col_bk1:
                df_y = ariza_df_getir()
                if not df_y.empty:
                    st.download_button("💾 Arıza DB", df_y.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), file_name=f"ariza_db_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
            with col_bk2:
                df_sy = stok_df_getir()
                if not df_sy.empty:
                    st.download_button("💾 Stok DB", df_sy.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"), file_name=f"stok_db_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)

        st.markdown("---")
        with st.expander("🗑️ Tehlikeli İşlemler (Veri Temizleme)"):
            st.warning("⚠️ Bu işlemler geri alınamaz!")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("🗑️ Kapalı Talepleri Temizle", use_container_width=True):
                    sb_delete("ariza_kayitlari", "durum=eq.Kapalı")
                    cache_temizle()
                    log_yaz("VERİ TEMİZLEME", "Kapalı talepler silindi")
                    st.success("Temizlendi.")
                    st.rerun()
            with col_d2:
                if st.button("🗑️ Sistem Logunu Temizle", use_container_width=True):
                    sb_delete("sistem_log", "id=gt.0")
                    st.success("Log temizlendi.")
                    st.rerun()

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align:center;padding:8px 0;font-size:11px;color:#334155;">
  TeknikPro CMMS v2.0 &nbsp;·&nbsp; TPM & Arıza Yönetim Platformu &nbsp;·&nbsp;
  <span style="color:#FFD700;">Enterprise Edition</span>
</div>""", unsafe_allow_html=True)
