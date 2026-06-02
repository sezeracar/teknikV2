# -*- coding: utf-8 -*-
"""
=============================================================================
TEKNIK BAKIM & ARIZA YÖNETİM SİSTEMİ v2.0
Enterprise-Grade TPM & CMMS Platform — Supabase Edition
=============================================================================
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, date, timedelta
import os
import hashlib
import json
import time
import requests

# =============================================================================
# SABITLER
# =============================================================================

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

# Geriye dönük uyumluluk
MAKINE_LISTESI = sorted(set(
    m for bl in MAKINE_LISTESI_BOLGE.values() for m in bl
))

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

# =============================================================================
# SUPABASE BAĞLANTI KATMANI
# =============================================================================

def sb_url() -> str:
    try:
        return st.secrets["supabase"]["url"]
    except Exception:
        return ""

def sb_key() -> str:
    try:
        return st.secrets["supabase"]["key"]
    except Exception:
        return ""

def sb_headers() -> dict:
    return {
        "apikey":        sb_key(),
        "Authorization": f"Bearer {sb_key()}",
        "Content-Type":  "application/json",
        "Prefer":        "return=representation"
    }

def secrets_kontrol() -> bool:
    try:
        u = st.secrets["supabase"]["url"]
        k = st.secrets["supabase"]["key"]
        if not u or not k:
            raise KeyError
        return True
    except (KeyError, FileNotFoundError):
        st.error("⚙️ **Supabase bağlantısı yapılandırılmamış.**")
        st.markdown("""
        **Kurulum adımları:**
        1. [share.streamlit.io](https://share.streamlit.io) → Uygulamanız → **⋮ → Settings → Secrets**
        2. Aşağıdaki içeriği yapıştırın ve kaydedin:
        ```toml
        [supabase]
        url = "https://PROJE_ADINIZ.supabase.co"
        key = "ANON_PUBLIC_KEY"
        ```
        3. Supabase değerleri için: **supabase.com → Projeniz → Project Settings → API**
        """)
        st.stop()
        return False

def sb_select(tablo: str, filtre: str = "") -> list:
    try:
        if not sb_url():
            return []
        url = f"{sb_url()}/rest/v1/{tablo}?{filtre}&order=id.desc" if filtre else               f"{sb_url()}/rest/v1/{tablo}?order=id.desc"
        r = requests.get(url, headers=sb_headers(), timeout=10)
        if r.ok:
            result = r.json()
            return result if isinstance(result, list) else []
        return []
    except Exception:
        return []

def sb_insert(tablo: str, veri: dict) -> bool:
    try:
        if not sb_url():
            return False
        url = f"{sb_url()}/rest/v1/{tablo}"
        r = requests.post(url, headers=sb_headers(), json=veri, timeout=10)
        return r.ok
    except Exception:
        return False

def sb_update(tablo: str, filtre: str, veri: dict) -> bool:
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

def sb_delete(tablo: str, filtre: str) -> bool:
    try:
        if not sb_url():
            return False
        url = f"{sb_url()}/rest/v1/{tablo}?{filtre}"
        r = requests.delete(url, headers=sb_headers(), timeout=10)
        return r.ok
    except Exception:
        return False

def sb_to_df(rows: list, kolon_map: dict = None) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    df = df.drop(columns=[c for c in ["id","created_at"] if c in df.columns])
    if kolon_map:
        df = df.rename(columns=kolon_map)
    for col in ["Stok Miktarı","Kritik Seviye","Maksimum Stok","Son Fiyat (TL)",
                "Çözüm Süresi (Dk)","Malzeme Maliyeti (TL)","İş Gücü Maliyeti (TL)","Toplam Maliyet (TL)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

ARIZA_KOLON_MAP = {
    "talep_no":            "Talep No",
    "bolge":               "Bölge",
    "durum":               "Durum",
    "oncelik":             "Öncelik",
    "vardiya":             "Vardiya",
    "acilis_tarihi":       "Açılış Tarihi",
    "kapatma_tarihi":      "Kapatma Tarihi",
    "bildiren":            "Bildiren",
    "bildiren_departman":  "Bildiren Departman",
    "mudahale_eden":       "Müdahale Eden",
    "makine":              "Makine",
    "ariza_turu":          "Arıza Türü",
    "alt_kategori":        "Alt Kategori",
    "ariza_tanimi":        "Arıza Tanımı",
    "bildirim_saati":      "Bildirim Saati",
    "ilk_mudahale_saati":  "İlk Müdahale Saati",
    "cozum_suresi_dk":     "Çözüm Süresi (Dk)",
    "sla_durumu":          "SLA Durumu",
    "cozum_aciklamasi":    "Çözüm Açıklaması",
    "kok_neden":           "Kök Neden",
    "bes_neden_analizi":   "5 Neden Analizi",
    "kaizen_onerisi":      "Kaizen Önerisi",
    "kullanilan_malzemeler": "Kullanılan Malzemeler",
    "malzeme_maliyeti":    "Malzeme Maliyeti (TL)",
    "isguc_maliyeti":      "İş Gücü Maliyeti (TL)",
    "toplam_maliyet":      "Toplam Maliyet (TL)",
    "fotograf_notu":       "Fotoğraf Notu",
    "kapatma_onayi":       "Kapatma Onayı",
}

STOK_KOLON_MAP = {
    "malzeme_kodu":   "Malzeme Kodu",
    "malzeme_adi":    "Malzeme Adı",
    "kategori":       "Kategori",
    "birim":          "Birim",
    "stok_miktari":   "Stok Miktarı",
    "kritik_seviye":  "Kritik Seviye",
    "maksimum_stok":  "Maksimum Stok",
    "son_fiyat":      "Son Fiyat (TL)",
    "tedarikci":      "Tedarikçi",
    "son_guncelleme": "Son Güncelleme",
}

@st.cache_data(ttl=5)
def ariza_df_getir() -> pd.DataFrame:
    try:
        rows = sb_select("ariza_kayitlari")
        return sb_to_df(rows, ARIZA_KOLON_MAP)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=10)
def stok_df_getir() -> pd.DataFrame:
    try:
        rows = sb_select("stok")
        return sb_to_df(rows, STOK_KOLON_MAP)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=60)
def kullanicilar_getir() -> dict:
    try:
        rows = sb_select("kullanicilar")
        if not rows:
            return {}
        return {r["kullanici_adi"]: {"sifre": r["sifre_hash"],
                                      "rol":   r["rol"],
                                      "tam_ad":r["tam_ad"]} for r in rows}
    except Exception:
        return {}

@st.cache_data(ttl=60)
def makine_listesi_db() -> dict:
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

@st.cache_data(ttl=60)
def ariza_turu_db() -> dict:
    try:
        rows = sb_select("ariza_turu_listesi", "aktif=eq.true")
        if not rows:
            return {}
        result = {}
        for r in rows:
            result.setdefault(r["kategori"], []).append(r["alt_tur"])
        return result
    except Exception:
        return {}

def aktif_makine_listesi() -> dict:
    db = makine_listesi_db()
    return db if db else MAKINE_LISTESI_BOLGE

def aktif_ariza_turleri() -> dict:
    db = ariza_turu_db()
    return db if db else ARIZA_TURLERI

def cache_temizle():
    ariza_df_getir.clear()
    stok_df_getir.clear()
    kullanicilar_getir.clear()
    makine_listesi_db.clear()
    ariza_turu_db.clear()

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
            {"malzeme_kodu":"M001","malzeme_adi":"VNA Sürüş Tekerleği (225mm)","kategori":"Hareketli Parça","birim":"Adet","stok_miktari":8,"kritik_seviye":2,"maksimum_stok":15,"son_fiyat":850,"tedarikci":"Jungheinrich TR","son_guncelleme":datetime.now().strftime("%d/%m/%Y")},
            {"malzeme_kodu":"M002","malzeme_adi":"RT Mesafe Sensörü (Sick)","kategori":"Sensör","birim":"Adet","stok_miktari":12,"kritik_seviye":3,"maksimum_stok":20,"son_fiyat":1200,"tedarikci":"Sick Türkiye","son_guncelleme":datetime.now().strftime("%d/%m/%Y")},
            {"malzeme_kodu":"M003","malzeme_adi":"PLC Dijital Giriş Modülü (Siemens)","kategori":"Elektrik","birim":"Adet","stok_miktari":4,"kritik_seviye":1,"maksimum_stok":8,"son_fiyat":2400,"tedarikci":"Siemens TR","son_guncelleme":datetime.now().strftime("%d/%m/%Y")},
            {"malzeme_kodu":"M004","malzeme_adi":"Rulman (6204-2RS)","kategori":"Mekanik","birim":"Adet","stok_miktari":25,"kritik_seviye":5,"maksimum_stok":50,"son_fiyat":45,"tedarikci":"SKF Türkiye","son_guncelleme":datetime.now().strftime("%d/%m/%Y")},
            {"malzeme_kodu":"M005","malzeme_adi":"Hidrolik Yağ ISO-46","kategori":"Sarf","birim":"Litre","stok_miktari":40,"kritik_seviye":10,"maksimum_stok":80,"son_fiyat":180,"tedarikci":"Shell TR","son_guncelleme":datetime.now().strftime("%d/%m/%Y")},
            {"malzeme_kodu":"M006","malzeme_adi":"Konveyör Kayışı (B-1500)","kategori":"Hareketli Parça","birim":"Metre","stok_miktari":30,"kritik_seviye":5,"maksimum_stok":60,"son_fiyat":95,"tedarikci":"ContiTech","son_guncelleme":datetime.now().strftime("%d/%m/%Y")},
            {"malzeme_kodu":"M007","malzeme_adi":"Motor Koruma Sigortası (16A)","kategori":"Elektrik","birim":"Adet","stok_miktari":20,"kritik_seviye":5,"maksimum_stok":40,"son_fiyat":35,"tedarikci":"ABB TR","son_guncelleme":datetime.now().strftime("%d/%m/%Y")},
            {"malzeme_kodu":"M008","malzeme_adi":"Endüstriyel Filtre Elemanı","kategori":"Sarf","birim":"Adet","stok_miktari":15,"kritik_seviye":3,"maksimum_stok":30,"son_fiyat":220,"tedarikci":"Parker TR","son_guncelleme":datetime.now().strftime("%d/%m/%Y")},
        ]
        for s in baslangic:
            sb_insert("stok", s)
    if not sb_select("kullanicilar"):
        for k in [
            {"kullanici_adi":"admin",    "sifre_hash":hashlib.sha256("1905".encode()).hexdigest(),"tam_ad":"Sistem Yöneticisi","rol":"Yönetici"},
            {"kullanici_adi":"sezer",    "sifre_hash":hashlib.sha256("1905".encode()).hexdigest(),"tam_ad":"Sezer Bey","rol":"Yönetici"},
            {"kullanici_adi":"teknik01", "sifre_hash":hashlib.sha256("1905".encode()).hexdigest(),"tam_ad":"Teknisyen 1","rol":"Teknisyen"},
            {"kullanici_adi":"uretim",   "sifre_hash":hashlib.sha256("1905".encode()).hexdigest(),"tam_ad":"Üretim Operatörü","rol":"Operatör"},
        ]:
            sb_insert("kullanicilar", k)

secrets_kontrol()
veritabani_hazirla()

# =============================================================================
# YARDIMCI FONKSİYONLAR
# =============================================================================

def log_yaz(islem: str, detay: str = ""):
    sb_insert("sistem_log", {
        "zaman":    datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "kullanici": st.session_state.get("aktif_kullanici", "Sistem"),
        "islem":    islem,
        "detay":    detay
    })

def sla_hesapla(oncelik: str, acilis: str, kapanis: str = None) -> dict:
    sla_dk = ARIZA_ONCELIKLERI.get(oncelik, {}).get("sla_dk", 480)
    try:
        ac    = datetime.strptime(acilis, "%d/%m/%Y %H:%M")
        bitis = datetime.strptime(kapanis, "%d/%m/%Y %H:%M") if kapanis else datetime.now()
        gecen = (bitis - ac).total_seconds() / 60
        return {"gecen_dk": int(gecen), "sla_dk": sla_dk,
                "oran": round(gecen/sla_dk*100,1),
                "durum": "✅ SLA İçinde" if gecen<=sla_dk else "⚠️ SLA Aşıldı"}
    except:
        return {"gecen_dk": 0, "sla_dk": sla_dk, "oran": 0, "durum": "—"}

def talep_no_uret() -> str:
    yil = datetime.now().year
    ay  = datetime.now().month
    prefix = f"ARZ-{yil}{ay:02d}-"
    rows = sb_select("ariza_kayitlari", f"talep_no=like.{prefix}*")
    return f"{prefix}{len(rows)+1:03d}"

def sifre_hashle(sifre: str) -> str:
    return hashlib.sha256(sifre.encode()).hexdigest()

def kullanicilari_yukle() -> dict:
    try:
        k = kullanicilar_getir()
        return k if k else KULLANICILAR_DEFAULT
    except:
        return KULLANICILAR_DEFAULT


# =============================================================================
# SAYFA KONFİGÜRASYONU & CSS
# =============================================================================

st.set_page_config(page_title="TeknikPro CMMS v2.0", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; font-size: 14px; }
.stApp { background: linear-gradient(160deg, #0f172a 0%, #1e293b 60%, #0f172a 100%) !important; }
[data-testid="stSidebar"] { background: linear-gradient(180deg, #0c1220 0%, #111827 100%) !important; border-right: 1px solid rgba(99,179,237,0.12) !important; }
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 { color: #93c5fd !important; }
[data-testid="metric-container"] { background: rgba(30,41,59,0.8) !important; border: 1px solid rgba(99,179,237,0.18) !important; border-radius: 12px !important; padding: 16px 20px !important; }
[data-testid="metric-container"] label { color: #94a3b8 !important; font-size: 12px !important; font-weight: 600 !important; text-transform: uppercase; }
[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #f1f5f9 !important; font-size: 28px !important; font-weight: 700 !important; }
h1 { color: #e2e8f0 !important; font-weight: 700 !important; font-size: 26px !important; }
h2 { color: #cbd5e1 !important; font-weight: 600 !important; }
h3 { color: #94a3b8 !important; font-weight: 600 !important; }
p, span, li { color: #cbd5e1 !important; }
label { color: #94a3b8 !important; font-size: 13px !important; }
[data-testid="stTabs"] [role="tablist"] { background: rgba(15,23,42,0.6) !important; border-radius: 10px !important; padding: 4px !important; border: 1px solid rgba(99,179,237,0.12) !important; }
[data-testid="stTabs"] [role="tab"] { color: #64748b !important; font-weight: 500 !important; font-size: 13px !important; border-radius: 8px !important; padding: 8px 16px !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { background: rgba(59,130,246,0.2) !important; color: #93c5fd !important; border: 1px solid rgba(99,179,237,0.35) !important; }
[data-testid="stTextInput"] input,[data-testid="stTextArea"] textarea { background: rgba(15,23,42,0.9) !important; border: 1px solid rgba(99,179,237,0.2) !important; border-radius: 8px !important; color: #e2e8f0 !important; }
[data-baseweb="popover"],[data-baseweb="popover"] * { background-color: #1e293b !important; color: #e2e8f0 !important; }
ul[role="listbox"] { background-color: #1e293b !important; border: 1px solid rgba(99,179,237,0.25) !important; border-radius: 8px !important; }
li[role="option"] { background-color: #1e293b !important; color: #e2e8f0 !important; }
li[role="option"]:hover,li[role="option"][aria-selected="true"] { background-color: #2d4a6e !important; color: #ffffff !important; }
[data-baseweb="menu"] { background-color: #1e293b !important; border: 1px solid rgba(99,179,237,0.25) !important; border-radius: 8px !important; }
[data-baseweb="menu"] li { color: #e2e8f0 !important; background-color: #1e293b !important; }
[data-baseweb="menu"] li:hover { background-color: #2d4a6e !important; color: #ffffff !important; }
[data-testid="stSelectbox"] [data-baseweb="select"] span,[data-testid="stSelectbox"] [data-baseweb="select"] div { color: #e2e8f0 !important; background-color: transparent !important; }
.stButton > button { background: linear-gradient(135deg, #1d4ed8, #2563eb) !important; color: #ffffff !important; border: none !important; border-radius: 8px !important; font-weight: 600 !important; }
[data-testid="stFormSubmitButton"] > button { background: linear-gradient(135deg, #059669, #10b981) !important; width: 100% !important; font-weight: 700 !important; border-radius: 10px !important; }
[data-testid="stDownloadButton"] > button { background: rgba(30,41,59,0.8) !important; border: 1px solid rgba(99,179,237,0.25) !important; color: #93c5fd !important; border-radius: 8px !important; }
[data-testid="stDataFrame"] { border: 1px solid rgba(99,179,237,0.12) !important; border-radius: 12px !important; }
[data-testid="stAlert"] { border-radius: 10px !important; border-left-width: 4px !important; }
[data-testid="stExpander"] { background: rgba(30,41,59,0.5) !important; border: 1px solid rgba(99,179,237,0.12) !important; border-radius: 10px !important; }
[data-testid="stNumberInput"] input { background: rgba(15,23,42,0.9) !important; border: 1px solid rgba(99,179,237,0.2) !important; border-radius: 8px !important; color: #e2e8f0 !important; }
hr { border-color: rgba(99,179,237,0.1) !important; }
.durum-karti { background: rgba(30,41,59,0.7); border: 1px solid rgba(99,179,237,0.15); border-radius: 12px; padding: 16px 20px; margin-bottom: 12px; }
.kritik-banner { background: linear-gradient(135deg, rgba(220,38,38,0.15), rgba(153,27,27,0.1)); border: 1px solid rgba(220,38,38,0.4); border-left: 4px solid #dc2626; border-radius: 10px; padding: 14px 18px; margin: 8px 0 16px 0; }
.sla-badge { display: inline-block; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; }
.sla-ok   { background: rgba(22,163,74,0.15);  border:1px solid rgba(22,163,74,0.4);  color:#4ade80; }
.sla-warn { background: rgba(220,38,38,0.15);  border:1px solid rgba(220,38,38,0.4);  color:#f87171; }
</style>
""", unsafe_allow_html=True)

# Dropdown JS fix
st.markdown("""
<script>
(function(){
  var css = `[data-baseweb="popover"]{background:#1e293b!important;}
  li[role="option"]{background:#1e293b!important;color:#e2e8f0!important;}
  li[role="option"]:hover{background:#2d4a6e!important;color:#fff!important;}`;
  var s=document.createElement("style");s.textContent=css;document.head.appendChild(s);
  new MutationObserver(function(){
    document.querySelectorAll('li[role="option"]').forEach(function(el){
      el.style.setProperty("background-color","#1e293b","important");
      el.style.setProperty("color","#e2e8f0","important");
    });
  }).observe(document.body,{childList:true,subtree:true});
})();
</script>
""", unsafe_allow_html=True)

# =============================================================================
# YETKİLENDİRME
# =============================================================================

def sidebar_giris():
    with st.sidebar:
        st.markdown("---")
        kullanicilar = kullanicilari_yukle()
        if not st.session_state.get("oturum_acik", False):
            st.markdown("### 🔐 Sistem Girişi")
            with st.form("sidebar_giris", clear_on_submit=True):
                k = st.text_input("Kullanıcı Adı", placeholder="kullanici_adi")
                s = st.text_input("Şifre", type="password", placeholder="••••••")
                giris = st.form_submit_button("Giriş Yap →", use_container_width=True)
                if giris:
                    k = k.strip().lower()
                    if k in kullanicilar and kullanicilar[k]["sifre"] == sifre_hashle(s):
                        st.session_state.oturum_acik     = True
                        st.session_state.aktif_kullanici = k
                        st.session_state.aktif_tam_ad    = kullanicilar[k]["tam_ad"]
                        st.session_state.aktif_rol       = kullanicilar[k]["rol"]
                        log_yaz("GİRİŞ", f"{kullanicilar[k]['tam_ad']} sisteme giriş yaptı")
                        st.rerun()
                    else:
                        st.error("Hatalı kimlik bilgileri.")
        else:
            tam_ad = st.session_state.aktif_tam_ad
            rol    = st.session_state.aktif_rol
            st.markdown(f"""
            <div style="background:rgba(30,58,138,0.2);border:1px solid rgba(99,179,237,0.25);
                        border-radius:10px;padding:14px 16px;margin-bottom:8px;">
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
                for k in ["oturum_acik","aktif_kullanici","aktif_tam_ad","aktif_rol"]:
                    st.session_state.pop(k, None)
                st.rerun()

def yetkili_mi(min_rol="Operatör") -> bool:
    ROL = {"Yönetici":3,"Teknisyen":2,"Operatör":1}
    return ROL.get(st.session_state.get("aktif_rol",""),0) >= ROL.get(min_rol,99)

def giris_gerektir(min_rol="Teknisyen") -> bool:
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
      <div style="font-size:20px;font-weight:800;color:#e2e8f0;line-height:1.2;">TeknikPro<br><span style="color:#3b82f6;">v2.0</span></div>
      <div style="font-size:11px;color:#475569;margin-top:6px;">TPM & Arıza Yönetim Platformu</div>
    </div>""", unsafe_allow_html=True)

    try:
        df_sb = ariza_df_getir()
        if not df_sb.empty and "Durum" in df_sb.columns:
            _acik   = len(df_sb[df_sb["Durum"]=="Açık"])
            _kritik = len(df_sb[(df_sb["Durum"]=="Açık") & (df_sb["Öncelik"].str.startswith("🔴",na=False))])
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

st.markdown("""
<div style="margin-bottom:24px;">
  <h1 style="margin:0;padding:0;">🛡️ Teknik Bakım & Arıza Yönetim Sistemi</h1>
  <p style="color:#475569;font-size:13px;margin-top:4px;">Computerized Maintenance Management System — Endüstriyel TPM Platformu</p>
</div>""", unsafe_allow_html=True)

tab_pano, tab_yeni, tab_kapat, tab_rapor, tab_stok, tab_ayar = st.tabs([
    "📊 Canlı Pano","➕ Yeni Talep Aç","✅ Talep Kapat",
    "📋 Raporlama & Arşiv","📦 Stok Yönetimi","⚙️ Sistem Ayarları"
])

# =============================================================================
# SEKME 1: CANLI PANO
# =============================================================================

with tab_pano:
    col_ref, _ = st.columns([1,6])
    with col_ref:
        if st.button("🔄 Yenile", use_container_width=True):
            ariza_df_getir.clear()
            st.rerun()

    df = ariza_df_getir()

    if df.empty or "Durum" not in df.columns:
        col1,col2,col3,col4,col5 = st.columns(5)
        with col1: st.metric("📋 Toplam Talep",0)
        with col2: st.metric("🟡 Açık Talepler",0)
        with col3: st.metric("✅ Kapatılan",0)
        with col4: st.metric("🔴 Kritik Açık",0)
        with col5: st.metric("⚠️ SLA Aşımı",0)
        st.info("📭 Sistemde henüz kayıt bulunmuyor.")
    else:
        toplam   = len(df)
        acik     = len(df[df["Durum"]=="Açık"])
        kapali   = len(df[df["Durum"]=="Kapalı"])
        kritik   = len(df[(df["Durum"]=="Açık") & (df["Öncelik"].str.startswith("🔴",na=False))])
        sla_asan = len(df[df["SLA Durumu"].str.contains("Aşıldı",na=False)])
        bugun    = datetime.now().strftime("%d/%m/%Y")
        bugun_s  = len(df[df["Açılış Tarihi"].str.startswith(bugun,na=False)]) if "Açılış Tarihi" in df.columns else 0

        col1,col2,col3,col4,col5 = st.columns(5)
        with col1: st.metric("📋 Toplam Talep", toplam, delta=f"+{bugun_s} bugün")
        with col2: st.metric("🟡 Açık Talepler", acik)
        with col3: st.metric("✅ Kapatılan", kapali, delta=f"%{round(kapali/max(toplam,1)*100)}")
        with col4: st.metric("🔴 Kritik Açık", kritik, delta="acil müdahale" if kritik>0 else "Temiz")
        with col5: st.metric("⚠️ SLA Aşımı", sla_asan)

        st.markdown("---")
        col_g1,col_g2 = st.columns(2)
        with col_g1:
            st.markdown("#### Öncelik Bazlı Açık Talepler")
            if acik > 0:
                adf = df[df["Durum"]=="Açık"]
                oc = adf["Öncelik"].value_counts()
                oc.index = [i[:30] for i in oc.index]
                st.bar_chart(oc, height=260)
            else:
                st.info("Açık talep yok")
        with col_g2:
            st.markdown("#### Makine Bazlı Arıza Sayısı")
            st.bar_chart(df["Makine"].value_counts().head(8), height=260)

        st.markdown("#### 30 Günlük Arıza Trendi")
        try:
            dt = df.copy()
            dt["Tarih"] = pd.to_datetime(dt["Açılış Tarihi"], format="%d/%m/%Y %H:%M", errors="coerce").dt.date
            dt = dt[dt["Tarih"] >= date.today()-timedelta(days=30)]
            gl = dt.groupby("Tarih").size().rename("Arıza Sayısı")
            if len(gl) > 0:
                st.line_chart(gl, height=200)
        except: pass

        st.markdown("---")
        st.markdown("#### 🟡 Müdahale Bekleyen Açık Talepler")
        adf2 = df[df["Durum"]=="Açık"].copy()
        if adf2.empty:
            st.success("✅ Açık talep bulunmuyor.")
        else:
            kdf = adf2[adf2["Öncelik"].str.startswith("🔴",na=False)]
            if not kdf.empty:
                st.markdown(f'''<div class="kritik-banner"><strong style="color:#f87171;">🚨 {len(kdf)} KRİTİK ARIZA acil müdahale bekliyor!</strong></div>''', unsafe_allow_html=True)
            gs = ["Talep No","Bölge","Öncelik","Açılış Tarihi","Bildiren","Makine","Arıza Türü","Arıza Tanımı","SLA Durumu"]
            gs = [s for s in gs if s in adf2.columns]
            st.dataframe(adf2[gs], use_container_width=True, hide_index=True)

# =============================================================================
# SEKME 2: YENİ TALEP AÇ
# =============================================================================

with tab_yeni:
    st.markdown("### ➕ Yeni Arıza Bildirimi Oluştur")
    st.caption("Bu form tüm personele açıktır. Oturum açmadan da kullanılabilir.")

    if not st.session_state.get("_talep_gonderildi", False):
        st.session_state["bil_saat"] = datetime.now().strftime("%H:%M")
    else:
        st.session_state["_talep_gonderildi"] = False

    # Bölge seçimi form dışında — makine listesini dinamik günceller
    secili_bolge = st.selectbox("🏭 Tesis / Bölge *", BOLGELER)

    with st.form("yeni_talep_formu", clear_on_submit=True):
        st.markdown("#### 👤 Bildiren Personel")
        col_b1,col_b2,col_b3 = st.columns(3)
        with col_b1:
            bildiren = st.text_input("Ad Soyad *", placeholder="Ahmet Yıldız")
        with col_b2:
            bildiren_dept = st.selectbox("Departman *", ["Üretim","Depo","Lojistik","Bakım","Kalite","İdari","Diğer"])
        with col_b3:
            vardiya = st.selectbox("Vardiya *", ["Gündüz (08:00–16:00)","Akşam (16:00–00:00)","Gece (00:00–08:00)"])

        st.markdown(f"#### 🏭 Arıza Lokasyonu — {secili_bolge}")
        col_m1,col_m2 = st.columns(2)
        mak_liste = aktif_makine_listesi().get(secili_bolge, MAKINE_LISTESI_BOLGE[secili_bolge])
        ariza_liste = aktif_ariza_turleri()
        with col_m1:
            makine    = st.selectbox("Makine / Sistem *", mak_liste)
            ariza_tur = st.selectbox("Arıza Kategorisi *", list(ariza_liste.keys()))
        with col_m2:
            oncelik      = st.selectbox("Kritiklik Seviyesi (SLA) *", list(ARIZA_ONCELIKLERI.keys()))
            bildirim_saat= st.text_input("Arıza Fark Edilme Saati", value=st.session_state.get("bil_saat", datetime.now().strftime("%H:%M")), help="SS:DD formatında")

        alt_kategori = st.selectbox("Alt Kategori", ariza_liste.get(ariza_tur, ["Diğer"]))
        ariza_tanimi = st.text_area("Arıza Tanımı *", placeholder="Arızanın belirti ve etkilerini açıklayın...", height=100)
        foto_notu    = st.text_input("Fotoğraf / Referans Notu", placeholder="Opsiyonel")

        sla_bilgi = ARIZA_ONCELIKLERI[oncelik]
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.6);border:1px solid rgba(99,179,237,0.15);border-radius:8px;padding:12px 16px;margin:8px 0;font-size:12px;">
          🏭 <strong style="color:#93c5fd;">Bölge:</strong> <span style="color:#fbbf24;">{secili_bolge}</span>
          &nbsp;&nbsp;|&nbsp;&nbsp;
          ⏱ <strong style="color:#93c5fd;">SLA Hedefi:</strong> <strong style="color:#fbbf24;">{sla_bilgi["sla_dk"]} dakika</strong>
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
                    st.success(f"✅ Talep **{no}** oluşturuldu! Bölge: {secili_bolge} | SLA: {sla_bilgi['sla_dk']} dk")
                    time.sleep(1)
                    st.rerun()
                else:
                    try:
                        url = f"{sb_url()}/rest/v1/ariza_kayitlari"
                        r = requests.post(url, headers=sb_headers(), json={
                            "talep_no": no, "bolge": secili_bolge, "durum": "Açık",
                            "oncelik": oncelik, "vardiya": vardiya,
                            "acilis_tarihi": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "bildiren": bildiren.strip(), "makine": makine,
                            "ariza_tanimi": ariza_tanimi.strip()
                        }, timeout=10)
                        st.error(f"❌ Supabase Hatası {r.status_code}: {r.text[:500]}")
                    except Exception as e:
                        st.error(f"❌ Bağlantı hatası: {e}")

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
            acik_k = df_k[df_k["Durum"]=="Açık"].copy()

            if acik_k.empty:
                st.success("🎉 Müdahale bekleyen açık talep bulunmuyor. Harika iş!")
            else:
                # Bölge filtresi
                bf = st.selectbox("🏭 Bölge Filtresi", ["Tüm Bölgeler"] + BOLGELER, key="kapat_bolge")
                if bf != "Tüm Bölgeler" and "Bölge" in acik_k.columns:
                    acik_k = acik_k[acik_k["Bölge"] == bf]

                if acik_k.empty:
                    st.info(f"ℹ️ {bf} bölgesinde açık talep bulunmuyor.")
                else:
                    krit_k = acik_k[acik_k["Öncelik"].str.startswith("🔴",na=False)]
                    if not krit_k.empty:
                        st.markdown(f'''<div class="kritik-banner"><strong style="color:#f87171;">🚨 {len(krit_k)} KRİTİK ARIZA — Acil müdahale bekliyor</strong></div>''', unsafe_allow_html=True)

                    col_s1, _ = st.columns([3,1])
                    with col_s1:
                        secenekler = acik_k.apply(
                            lambda r: f"[{r['Talep No']}] {str(r.get('Bölge',''))[:10]} | {r['Öncelik'][:2]} {r['Makine']} — {str(r['Arıza Tanımı'])[:50]}",
                            axis=1
                        ).tolist()
                        secilen = st.selectbox("📋 Kapatılacak Talebi Seçin", secenekler)

                    secilen_no = secilen.split("]")[0].replace("[","").strip()
                    talep_df2  = df_k[df_k["Talep No"]==secilen_no]
                    if talep_df2.empty:
                        st.error("Talep bulunamadı.")
                        st.stop()
                    talep = talep_df2.iloc[0]

                    sla_g  = sla_hesapla(talep["Öncelik"], talep["Açılış Tarihi"])
                    sla_cls= "sla-ok" if "İçinde" in sla_g["durum"] else "sla-warn"
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

                    with st.form("kapat_formu"):
                        col_k1,col_k2,col_k3 = st.columns(3)
                        with col_k1:
                            mudahale_eden = st.text_input("Müdahale Eden Teknisyen *", value=st.session_state.get("aktif_tam_ad",""))
                        with col_k2:
                            mud_bas = st.text_input("🕐 Başlama Saati *", value=datetime.now().strftime("%H:%M"), help="SS:DD")
                        with col_k3:
                            mud_bit = st.text_input("🕑 Bitiş Saati *", value=datetime.now().strftime("%H:%M"), help="SS:DD")

                        try:
                            bd = datetime.strptime(date.today().strftime("%d/%m/%Y")+" "+mud_bas.strip(), "%d/%m/%Y %H:%M")
                            btt= datetime.strptime(date.today().strftime("%d/%m/%Y")+" "+mud_bit.strip(), "%d/%m/%Y %H:%M")
                            if btt < bd: btt += timedelta(days=1)
                            cozum_dk = max(1, int((btt-bd).total_seconds()/60))
                            parse_ok = True
                        except:
                            cozum_dk = 1
                            parse_ok = False

                        isguc = round((cozum_dk/60)*ISCI_UCRET, 2)
                        if parse_ok:
                            st.info(f"⏱ Çözüm Süresi: **{cozum_dk} dk** ({cozum_dk//60}s {cozum_dk%60}dk)  |  💰 İş Gücü: **{isguc:,.0f} TL** (300 TL/saat)")
                        else:
                            st.warning("⚠️ Saat formatı hatalı. SS:DD formatında girin.")

                        col_k4,col_k5 = st.columns(2)
                        with col_k4:
                            kok_neden = st.selectbox("Kök Neden", ["Yağlama eksikliği","Aşınma (ömür tükenmesi)","Hatalı kullanım","Yetersiz bakım periyodu","Tasarım/malzeme yetersizliği","Dış etken (toz, nem, darbe)","Yazılım/donanım arızası","Bilinmiyor","Diğer"])
                        with col_k5:
                            kapat_onayi = st.selectbox("Kapatma Onayı", ["Teknisyen Onayı","Vardiya Amiri Onayı","Bakım Müdürü Onayı"])

                        cozum_aciklama = st.text_area("Uygulanan Çözüm & Teknik Notlar *", height=90)
                        neden_analizi  = st.text_area("5 Neden Analizi", height=90)
                        kaizen         = st.text_area("Kaizen / İyileştirme Önerisi", height=70)

                        st.markdown("#### 📦 Kullanılan Malzeme")
                        df_stok_k = stok_df_getir()
                        stok_sec = ["—  Malzeme Kullanılmadı"]
                        if not df_stok_k.empty and "Malzeme Adı" in df_stok_k.columns:
                            stok_sec += df_stok_k["Malzeme Adı"].tolist()

                        col_stk1,col_stk2,col_stk3 = st.columns(3)
                        with col_stk1: malzeme_secim  = st.selectbox("Stoktan Malzeme", stok_sec)
                        with col_stk2: malzeme_adet   = st.number_input("Kullanılan Miktar", min_value=0, step=1, value=0)
                        with col_stk3: malzeme_maliyet= st.number_input("Malzeme Maliyeti (TL)", min_value=0, step=50, value=0)

                        submit_kapat = st.form_submit_button("✅ Talebi Kapat & Kaydet", use_container_width=True)

                        if submit_kapat:
                            if not mudahale_eden.strip():
                                st.error("❌ Teknisyen adı zorunludur.")
                            elif not parse_ok:
                                st.error("❌ Saat formatı hatalı.")
                            elif not cozum_aciklama.strip():
                                st.error("❌ Çözüm açıklaması zorunludur.")
                            else:
                                malzeme_metni = "—"
                                if "—" not in malzeme_secim and malzeme_adet > 0 and not df_stok_k.empty:
                                    stok_satir = df_stok_k[df_stok_k["Malzeme Adı"]==malzeme_secim]
                                    if not stok_satir.empty:
                                        stok_mik = int(stok_satir["Stok Miktarı"].values[0])
                                        if stok_mik < malzeme_adet:
                                            st.error(f"❌ Yetersiz stok! Mevcut: {stok_mik}")
                                            st.stop()
                                        sb_update("stok", f"malzeme_adi=eq.{malzeme_secim}", {
                                            "stok_miktari": stok_mik - malzeme_adet,
                                            "son_guncelleme": datetime.now().strftime("%d/%m/%Y")
                                        })
                                    malzeme_metni = f"{malzeme_secim} x {malzeme_adet}"

                                toplam_maliyet = isguc + malzeme_maliyet
                                kapat_zaman = datetime.now().strftime("%d/%m/%Y %H:%M")
                                sla_s = sla_hesapla(talep["Öncelik"], talep["Açılış Tarihi"], kapat_zaman)

                                sb_update("ariza_kayitlari", f"talep_no=eq.{secilen_no}", {
                                    "durum":"Kapalı","kapatma_tarihi":kapat_zaman,
                                    "mudahale_eden":mudahale_eden.strip(),
                                    "ilk_mudahale_saati":f"{mud_bas.strip()} - {mud_bit.strip()}",
                                    "cozum_suresi_dk":int(cozum_dk),"sla_durumu":sla_s["durum"],
                                    "cozum_aciklamasi":cozum_aciklama.strip(),"kok_neden":str(kok_neden),
                                    "bes_neden_analizi":neden_analizi,"kaizen_onerisi":kaizen,
                                    "kullanilan_malzemeler":malzeme_metni,
                                    "malzeme_maliyeti":float(malzeme_maliyet),
                                    "isguc_maliyeti":float(isguc),"toplam_maliyet":float(toplam_maliyet),
                                    "kapatma_onayi":str(kapat_onayi),
                                })
                                cache_temizle()
                                log_yaz("TALEP KAPATILDI", f"{secilen_no} — {mudahale_eden} — {cozum_dk} dk — {toplam_maliyet:.0f} TL")
                                st.success(f"✅ Talep **{secilen_no}** kapatıldı! Süre: {cozum_dk} dk | Toplam: {toplam_maliyet:,.0f} TL | {sla_s['durum']}")
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
            col_f1,col_f2,col_f3,col_f4,col_f5 = st.columns(5)
            with col_f1: f_bolge   = st.selectbox("Bölge",      ["Tümü"]+BOLGELER)
            with col_f2: f_durum   = st.selectbox("Durum",      ["Tümü","Açık","Kapalı"])
            with col_f3: f_oncelik = st.selectbox("Öncelik",    ["Tümü"]+list(ARIZA_ONCELIKLERI.keys()))
            with col_f4: f_makine  = st.selectbox("Makine",     ["Tümü"]+MAKINE_LISTESI)
            with col_f5: f_tur     = st.selectbox("Arıza Türü", ["Tümü"]+list(ARIZA_TURLERI.keys()))
            col_t1,col_t2,col_t3 = st.columns([2,2,2])
            with col_t1: f_bas   = st.date_input("Başlangıç", date(2025,1,1))
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
                    mask = g.apply(lambda r: r.astype(str).str.contains(f_arama,case=False,na=False).any(), axis=1)
                    g = g[mask]
                except: pass
            try:
                if "Açılış Tarihi" in g.columns:
                    g["_t"] = pd.to_datetime(g["Açılış Tarihi"], format="%d/%m/%Y %H:%M", errors="coerce").dt.date
                    g = g[(g["_t"]>=f_bas)&(g["_t"]<=f_bit)].drop(columns=["_t"])
            except: pass

            col_oz1,col_oz2,col_oz3,col_oz4 = st.columns(4)
            with col_oz1: st.metric("Kayıt Sayısı", len(g))
            with col_oz2:
                try: os_ = round(pd.to_numeric(g["Çözüm Süresi (Dk)"],errors="coerce").dropna().mean())
                except: os_ = "—"
                st.metric("Ort. Çözüm Süresi", f"{os_} dk" if isinstance(os_,(int,float)) else "—")
            with col_oz3:
                try: tm = pd.to_numeric(g["Toplam Maliyet (TL)"],errors="coerce").sum()
                except: tm = 0
                st.metric("Toplam Maliyet", f"{tm:,.0f} ₺")
            with col_oz4:
                try: sa = len(g[g["SLA Durumu"].str.contains("Aşıldı",na=False)])
                except: sa = 0
                st.metric("SLA Aşımı", sa)

            col_dl1,_ = st.columns([1,4])
            with col_dl1:
                st.download_button("📥 CSV İndir",
                    g.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"),
                    file_name=f"ariza_raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", mime="text/csv")

            if not g.empty:
                try:    st.dataframe(g.sort_values("Açılış Tarihi",ascending=False), use_container_width=True, hide_index=True)
                except: st.dataframe(g, use_container_width=True, hide_index=True)

            if len(g)>0 and "Talep No" in g.columns:
                with st.expander("📄 Talep Detay"):
                    sn = st.selectbox("Talep seçin", g["Talep No"].tolist())
                    sr = g[g["Talep No"]==sn]
                    if not sr.empty:
                        s = sr.iloc[0]
                        col_d1,col_d2 = st.columns(2)
                        alanlar = [a for a in ARIZA_SUTUNLARI if a in s.index]
                        yari = len(alanlar)//2
                        with col_d1:
                            for a in alanlar[:yari]:
                                if str(s[a]) not in ["","nan","0","0.0"]: st.markdown(f"**{a}:** {s[a]}")
                        with col_d2:
                            for a in alanlar[yari:]:
                                if str(s[a]) not in ["","nan","0","0.0"]: st.markdown(f"**{a}:** {s[a]}")

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
            kritik_stok = df_st[df_st["Stok Miktarı"]<=df_st["Kritik Seviye"]]
            for _,row in kritik_stok.iterrows():
                st.markdown(f'''<div class="kritik-banner">⚠️ <strong style="color:#fbbf24;">ACİL SİPARİŞ:</strong> <span style="color:#cbd5e1;">{row["Malzeme Adı"]}</span> — Mevcut: <strong style="color:#f87171;">{row["Stok Miktarı"]} {row.get("Birim","adet")}</strong> / Kritik: {row["Kritik Seviye"]}</div>''', unsafe_allow_html=True)

            if df_st["Maksimum Stok"].sum() > 0:
                df_st2 = df_st.copy()
                df_st2["Doluluk %"] = (df_st2["Stok Miktarı"]/df_st2["Maksimum Stok"].replace(0,1)*100).round(1).clip(upper=100)
                st.markdown("#### Stok Doluluk Oranları")
                st.bar_chart(df_st2.set_index("Malzeme Adı")["Doluluk %"], height=240)

            col_tbl,col_form = st.columns([3,2])

            with col_tbl:
                st.markdown("#### Güncel Envanter Tablosu")
                gsc = [s for s in STOK_SUTUNLARI if s in df_st.columns]
                st.dataframe(df_st[gsc], use_container_width=True, hide_index=True)
                st.download_button("📥 Envanter İndir",
                    df_st.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"),
                    file_name=f"stok_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

            with col_form:
                st.markdown("#### 🔧 Stok Güncelle")
                with st.form("stok_guncelle"):
                    secilen_mal = st.selectbox("Malzeme", df_st["Malzeme Adı"].tolist())
                    islem_tipi  = st.radio("İşlem", ["Stok Girişi (Ekleme)","Stok Çıkışı (Kullanım)","Mutlak Değer Gir"])
                    miktar      = st.number_input("Miktar", min_value=0, step=1, value=0)
                    st.text_input("Not", placeholder="Opsiyonel")
                    if st.form_submit_button("💾 Kaydet", use_container_width=True):
                        ds2  = stok_df_getir()
                        ms2  = ds2["Malzeme Adı"]==secilen_mal
                        mev  = int(ds2.loc[ms2,"Stok Miktarı"].values[0])
                        if "Ekleme" in islem_tipi: yeni_m = mev+miktar
                        elif "Çıkış" in islem_tipi:
                            if mev<miktar: st.error(f"❌ Yetersiz stok! Mevcut:{mev}"); st.stop()
                            yeni_m = mev-miktar
                        else: yeni_m = miktar
                        sb_update("stok",f"malzeme_adi=eq.{secilen_mal}",{"stok_miktari":int(yeni_m),"son_guncelleme":datetime.now().strftime("%d/%m/%Y")})
                        cache_temizle()
                        log_yaz("STOK GÜNCELLEME",f"{secilen_mal} {mev}→{yeni_m}")
                        st.success(f"✅ {secilen_mal}: {mev} → **{yeni_m}**")
                        time.sleep(1); st.rerun()

                if yetkili_mi("Yönetici"):
                    st.markdown("---")

                    # Excel/CSV toplu yükleme
                    st.markdown("#### 📂 Excel/CSV Toplu Yükleme")
                    sablon = pd.DataFrame(columns=["Malzeme Kodu","Malzeme Adı","Kategori","Birim","Stok Miktarı","Kritik Seviye","Maksimum Stok","Son Fiyat (TL)","Tedarikçi"])
                    st.download_button("📥 Şablon İndir", sablon.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"), file_name="stok_sablon.csv", mime="text/csv")

                    yukle_dosya = st.file_uploader("Excel (.xlsx) veya CSV (.csv)", type=["xlsx","csv"], key="stok_yukle")
                    if yukle_dosya:
                        try:
                            df_yukle = pd.read_excel(yukle_dosya,dtype=str) if yukle_dosya.name.endswith(".xlsx") else pd.read_csv(yukle_dosya,dtype=str)
                            st.markdown(f"**{len(df_yukle)} satır okundu.** Önizleme:")
                            st.dataframe(df_yukle.head(5), use_container_width=True, hide_index=True)
                            mod = st.radio("Yükleme Modu", ["Yeni ekle (var olanı atla)","Güncelle (stok miktarını yaz)"], key="yukle_mod")
                            if st.button("🚀 Yüklemeyi Başlat"):
                                dm  = stok_df_getir()
                                ek=gu=at=0
                                for _,sr in df_yukle.iterrows():
                                    kod = str(sr.get("Malzeme Kodu","")).strip()
                                    ad  = str(sr.get("Malzeme Adı","")).strip()
                                    if not ad: continue
                                    mev_mi = not dm.empty and (dm["Malzeme Kodu"]==kod).any()
                                    veri = {
                                        "malzeme_kodu":kod,"malzeme_adi":ad,
                                        "kategori":str(sr.get("Kategori","Diğer")).strip(),
                                        "birim":str(sr.get("Birim","Adet")).strip(),
                                        "stok_miktari":float(str(sr.get("Stok Miktarı",0)).replace(",",".")or 0),
                                        "kritik_seviye":float(str(sr.get("Kritik Seviye",0)).replace(",",".")or 0),
                                        "maksimum_stok":float(str(sr.get("Maksimum Stok",0)).replace(",",".")or 0),
                                        "son_fiyat":float(str(sr.get("Son Fiyat (TL)",0)).replace(",",".")or 0),
                                        "tedarikci":str(sr.get("Tedarikçi","")).strip(),
                                        "son_guncelleme":datetime.now().strftime("%d/%m/%Y")
                                    }
                                    if mev_mi:
                                        if "Güncelle" in mod:
                                            sb_update("stok",f"malzeme_kodu=eq.{kod}",{"stok_miktari":veri["stok_miktari"],"son_guncelleme":veri["son_guncelleme"]})
                                            gu+=1
                                        else: at+=1
                                    else:
                                        sb_insert("stok",veri); ek+=1
                                cache_temizle()
                                log_yaz("TOPLU STOK",f"Ek:{ek} Gün:{gu} Atl:{at}")
                                st.success(f"✅ {ek} eklendi, {gu} güncellendi, {at} atlandı.")
                                time.sleep(1); st.rerun()
                        except Exception as e:
                            st.error(f"❌ Dosya okunamadı: {e}")

                    st.markdown("---")
                    st.markdown("#### ➕ Yeni Malzeme Tanımla")
                    with st.form("yeni_malzeme"):
                        col_nm1,col_nm2 = st.columns(2)
                        with col_nm1:
                            y_kod  = st.text_input("Malzeme Kodu", placeholder="M009")
                            y_ad   = st.text_input("Malzeme Adı")
                            y_kat  = st.selectbox("Kategori", ["Hareketli Parça","Sensör","Elektrik","Mekanik","Sarf","Hidrolik","Elektronik","Diğer"])
                            y_bir  = st.selectbox("Birim", ["Adet","Litre","Metre","Kg","Rulo","Kutu","Set","Takım"])
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
                                sb_insert("stok",{"malzeme_kodu":y_kod,"malzeme_adi":y_ad.strip(),"kategori":y_kat,"birim":y_bir,"stok_miktari":int(y_stok),"kritik_seviye":int(y_krit),"maksimum_stok":int(y_maks),"son_fiyat":float(y_fiyat),"tedarikci":y_tedarik,"son_guncelleme":datetime.now().strftime("%d/%m/%Y")})
                                cache_temizle()
                                log_yaz("YENİ MALZEME",f"{y_kod} — {y_ad}")
                                st.success(f"✅ {y_ad} eklendi!")
                                time.sleep(1); st.rerun()

# =============================================================================
# SEKME 6: SİSTEM AYARLARI
# =============================================================================

with tab_ayar:
    if not giris_gerektir("Yönetici"):
        pass
    else:
        st.markdown("### ⚙️ Sistem Ayarları & Kullanıcı Yönetimi")
        col_a1,col_a2 = st.columns(2)

        with col_a1:
            st.markdown("#### 👥 Kullanıcı Listesi")
            kullanicilar = kullanicilari_yukle()
            for k_ad,k_bilgi in kullanicilar.items():
                st.markdown(f'''<div class="durum-karti" style="padding:12px 16px;margin-bottom:8px;">
                  <span style="font-weight:600;color:#e2e8f0;">{k_bilgi["tam_ad"]}</span>
                  <span style="font-size:12px;color:#64748b;margin-left:8px;">@{k_ad}</span>
                  <span class="sla-badge sla-ok" style="margin-left:8px;">{k_bilgi["rol"]}</span>
                </div>''', unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### ✏️ Kullanıcı Düzenle")
            with st.form("kullanici_duzenle"):
                duz_sec = st.selectbox("Düzenlenecek", list(kullanicilar.keys()), format_func=lambda k: f"{kullanicilar[k]['tam_ad']} (@{k})")
                col_d1,col_d2 = st.columns(2)
                with col_d1:
                    duz_ad  = st.text_input("Ad Soyad", value=kullanicilar[duz_sec]["tam_ad"])
                    duz_rol = st.selectbox("Rol", ["Operatör","Teknisyen","Yönetici"], index=["Operatör","Teknisyen","Yönetici"].index(kullanicilar[duz_sec]["rol"]))
                with col_d2:
                    duz_s1 = st.text_input("Yeni Şifre", type="password", placeholder="••••••")
                    duz_s2 = st.text_input("Şifre Tekrar", type="password", placeholder="••••••")
                if st.form_submit_button("💾 Kaydet", use_container_width=True):
                    if duz_s1 and duz_s1!=duz_s2:
                        st.error("❌ Şifreler eşleşmiyor!")
                    else:
                        gv = {"tam_ad":duz_ad.strip()or kullanicilar[duz_sec]["tam_ad"],"rol":duz_rol}
                        if duz_s1: gv["sifre_hash"] = sifre_hashle(duz_s1)
                        sb_update("kullanicilar",f"kullanici_adi=eq.{duz_sec}",gv)
                        cache_temizle()
                        log_yaz("KULLANICI GÜNCELLENDİ",f"{duz_sec}→{duz_rol}")
                        st.success(f"✅ {duz_sec} güncellendi!")
                        st.rerun()

            st.markdown("---")
            st.markdown("#### 🗑️ Kullanıcı Sil")
            with st.form("kullanici_sil"):
                ak = st.session_state.get("aktif_kullanici","")
                silinebilir = {k:v for k,v in kullanicilar.items() if k!=ak}
                sil_sec = st.selectbox("Silinecek", list(silinebilir.keys()), format_func=lambda k: f"{silinebilir[k]['tam_ad']} (@{k})") if silinebilir else None
                if st.form_submit_button("🗑️ Sil", use_container_width=True) and sil_sec:
                    sb_delete("kullanicilar",f"kullanici_adi=eq.{sil_sec}")
                    cache_temizle()
                    log_yaz("KULLANICI SİLİNDİ",sil_sec)
                    st.success(f"✅ {sil_sec} silindi.")
                    st.rerun()

            st.markdown("---")
            st.markdown("#### ➕ Yeni Kullanıcı Ekle")
            with st.form("yeni_kullanici"):
                col_u1,col_u2 = st.columns(2)
                with col_u1:
                    y_kul  = st.text_input("Kullanıcı Adı")
                    y_sif  = st.text_input("Şifre", type="password")
                with col_u2:
                    y_ad2  = st.text_input("Ad Soyad")
                    y_rol2 = st.selectbox("Rol", ["Operatör","Teknisyen","Yönetici"])
                if st.form_submit_button("Kullanıcı Oluştur", use_container_width=True):
                    if not all([y_kul,y_sif,y_ad2]): st.error("Tüm alanlar zorunludur.")
                    elif y_kul.lower() in kullanicilar: st.error("Bu kullanıcı adı zaten mevcut.")
                    else:
                        sb_insert("kullanicilar",{"kullanici_adi":y_kul.lower(),"sifre_hash":sifre_hashle(y_sif),"rol":y_rol2,"tam_ad":y_ad2})
                        cache_temizle()
                        log_yaz("KULLANICI OLUŞTURULDU",f"{y_kul} — {y_rol2}")
                        st.success(f"✅ {y_ad2} ({y_rol2}) oluşturuldu!")
                        st.rerun()

        with col_a2:
            # Makine Yönetimi
            st.markdown("#### 🏭 Makine Listesi Yönetimi")
            with st.expander("Makine Ekle / Sil", expanded=False):
                mk_rows = sb_select("makine_listesi","aktif=eq.true")
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
                        sb_insert("makine_listesi",{"bolge":m_bolge,"makine_adi":m_ad.strip(),"aktif":True})
                        cache_temizle()
                        log_yaz("MAKİNE EKLENDİ",f"{m_bolge} — {m_ad}")
                        st.success(f"✅ {m_ad} eklendi!"); st.rerun()
                if mk_rows:
                    sil_dict = {f"{r['bolge']} — {r['makine_adi']}":r["id"] for r in mk_rows}
                    col_ms1,col_ms2 = st.columns([3,1])
                    with col_ms1: sil_mk = st.selectbox("Silinecek", list(sil_dict.keys()), key="mk_sil")
                    with col_ms2:
                        st.markdown("<br>",unsafe_allow_html=True)
                        if st.button("🗑️",key="mk_sil_btn"):
                            sb_delete("makine_listesi",f"id=eq.{sil_dict[sil_mk]}")
                            cache_temizle()
                            st.success("Silindi!"); st.rerun()

            # Arıza Türü Yönetimi
            st.markdown("#### ⚙️ Arıza Türü Yönetimi")
            with st.expander("Arıza Türü Ekle / Sil", expanded=False):
                at_rows = sb_select("ariza_turu_listesi","aktif=eq.true")
                if at_rows:
                    df_at = pd.DataFrame(at_rows)[["kategori","alt_tur"]]
                    df_at.columns = ["Kategori","Alt Tür"]
                    st.dataframe(df_at, use_container_width=True, hide_index=True)
                else:
                    st.caption("Henüz eklenmemiş — sabit liste kullanılıyor.")
                mevcut_kat = list(ARIZA_TURLERI.keys())
                if at_rows:
                    mevcut_kat = sorted(set(mevcut_kat+list({r["kategori"] for r in at_rows})))
                with st.form("ariza_turu_ekle"):
                    at_kat_sec = st.selectbox("Kategori", ["— Yeni kategori gir —"]+mevcut_kat, key="atk")
                    at_kat_yeni= st.text_input("Yeni Kategori (opsiyonel)", placeholder="Örn: 🔩 Bağlantı")
                    at_alt     = st.text_input("Alt Tür", placeholder="Örn: Cıvata gevşemesi")
                    if st.form_submit_button("➕ Ekle", use_container_width=True) and at_alt.strip():
                        kat = at_kat_yeni.strip() if at_kat_sec=="— Yeni kategori gir —" else at_kat_sec
                        if kat:
                            sb_insert("ariza_turu_listesi",{"kategori":kat,"alt_tur":at_alt.strip(),"aktif":True})
                            cache_temizle()
                            log_yaz("ARIZA TÜRÜ EKLENDİ",f"{kat} — {at_alt}")
                            st.success(f"✅ {kat} → {at_alt}"); st.rerun()
                if at_rows:
                    sil_at = {f"{r['kategori']} — {r['alt_tur']}":r["id"] for r in at_rows}
                    col_as1,col_as2 = st.columns([3,1])
                    with col_as1: sil_at_sec = st.selectbox("Silinecek", list(sil_at.keys()), key="at_sil")
                    with col_as2:
                        st.markdown("<br>",unsafe_allow_html=True)
                        if st.button("🗑️",key="at_sil_btn"):
                            sb_delete("ariza_turu_listesi",f"id=eq.{sil_at[sil_at_sec]}")
                            cache_temizle()
                            st.success("Silindi!"); st.rerun()

            st.markdown("---")
            st.markdown("#### 📜 Sistem Aktivite Logu")
            try:
                log_rows = sb_select("sistem_log")
                if log_rows:
                    df_log = pd.DataFrame(log_rows).rename(columns={"zaman":"Zaman","kullanici":"Kullanıcı","islem":"İşlem","detay":"Detay"})
                    st.dataframe(df_log.sort_values("Zaman",ascending=False).head(50), use_container_width=True, hide_index=True)
                    st.download_button("📥 Log İndir", df_log.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"), file_name=f"log_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")
                else:
                    st.info("Henüz log kaydı yok.")
            except Exception as e:
                st.info(f"Log yüklenemedi: {e}")

            st.markdown("---")
            st.markdown("#### 🗄️ Veri Yedekleme")
            col_bk1,col_bk2 = st.columns(2)
            with col_bk1:
                df_y = ariza_df_getir()
                if not df_y.empty:
                    st.download_button("💾 Arıza DB", df_y.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"), file_name=f"ariza_db_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)
            with col_bk2:
                df_sy = stok_df_getir()
                if not df_sy.empty:
                    st.download_button("💾 Stok DB", df_sy.to_csv(index=False,encoding="utf-8-sig").encode("utf-8-sig"), file_name=f"stok_db_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True)

        st.markdown("---")
        with st.expander("🗑️ Tehlikeli İşlemler (Veri Temizleme)"):
            st.warning("⚠️ Bu işlemler geri alınamaz!")
            col_d1,col_d2 = st.columns(2)
            with col_d1:
                if st.button("🗑️ Kapalı Talepleri Temizle", use_container_width=True):
                    sb_delete("ariza_kayitlari","durum=eq.Kapalı")
                    cache_temizle()
                    log_yaz("VERİ TEMİZLEME","Kapalı talepler silindi")
                    st.success("Temizlendi."); st.rerun()
            with col_d2:
                if st.button("🗑️ Sistem Logunu Temizle", use_container_width=True):
                    sb_delete("sistem_log","id=gt.0")
                    st.success("Log temizlendi."); st.rerun()

# =============================================================================
# FOOTER
# =============================================================================

st.markdown("---")
st.markdown("""
<div style="text-align:center;padding:8px 0;font-size:11px;color:#334155;">
  TeknikPro CMMS v2.0 &nbsp;·&nbsp; TPM & Arıza Yönetim Platformu &nbsp;·&nbsp;
  <span style="color:#1d4ed8;">Enterprise Edition</span>
</div>""", unsafe_allow_html=True)
