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
        # VNA
        "VNA-01 (Hat A)", "VNA-02 (Hat A)", "VNA-03 (Hat B)", "VNA-04 (Hat B)",
        # Reach Truck
        "RT-01 (Depo Sahası)", "RT-02 (Depo Sahası)", "RT-03 (Depo Sahası)",
        # Konveyör
        "Konveyör Hattı 1", "Konveyör Hattı 2", "Konveyör Hattı 3",
        # Altyapı
        "Kompresör İstasyonu", "Elektrik Panosu MCC-1", "Elektrik Panosu MCC-2",
        "Soğutma Ünitesi", "Jeneratör",
        # Taşıma
        "Forklift FLT-01", "Forklift FLT-02", "Transpalet-01", "Transpalet-02",
        # Diğer
        "Şarj İstasyonu Adana", "Kapı Otomasyonu", "Yangın Sistemi Adana", "Diğer"
    ],
    "🏭 Tuzla LM": [
        # VNA
        "VNA-01 (Tuzla)", "VNA-02 (Tuzla)", "VNA-03 (Tuzla)",
        # Reach Truck
        "RT-01 (Tuzla Depo)", "RT-02 (Tuzla Depo)",
        # Konveyör
        "Konveyör Hattı 1 (Tuzla)", "Konveyör Hattı 2 (Tuzla)",
        # Altyapı
        "Kompresör İstasyonu (Tuzla)", "Elektrik Panosu MCC-1 (Tuzla)",
        "Soğutma Ünitesi (Tuzla)", "Jeneratör (Tuzla)",
        # Taşıma
        "Forklift FLT-01 (Tuzla)", "Forklift FLT-02 (Tuzla)",
        "Transpalet-01 (Tuzla)", "Transpalet-02 (Tuzla)",
        # Diğer
        "Şarj İstasyonu Tuzla", "Kapı Otomasyonu (Tuzla)",
        "Yangın Sistemi Tuzla", "Diğer"
    ]
}

# Geriye dönük uyumluluk için düz liste (eski kayıtlar için)
MAKINE_LISTESI = list(set(
    MAKINE_LISTESI_BOLGE["🏭 Adana LM"] +
    MAKINE_LISTESI_BOLGE["🏭 Tuzla LM"]
))

ARIZA_TURLERI = {
    "⚡ Elektrik": [
        "Sigorta attı", "Motor arızası", "Sensör hatası", "PLC/Otomasyon hatası",
        "Kablo kopması", "Kontaktör arızası", "Enkoder arızası", "Frekans sürücü hatası",
        "Akü/Şarj sorunu", "Topraklama hatası", "Diğer"
    ],
    "⚙️ Mekanik": [
        "Rulman arızası", "Kayış/Zincir kopması", "Dişli hasarı", "Aşınma",
        "Titreşim/Gürültü", "Mil kırılması", "Sabitleme/Bağlantı sorunu",
        "Sızdırmazlık arızası", "Fren arızası", "Lastik/Tekerlek hasarı", "Diğer"
    ],
    "🔧 Tesisat / Hidrolik": [
        "Boru sızıntısı", "Valf arızası", "Pompa sorunu", "Basınç düşüklüğü",
        "Hidrolik yağ kaçağı", "Filtre tıkanması", "Pnömatik hat sorunu", "Diğer"
    ],
    "🖥️ Elektronik / Yazılım": [
        "HMI ekran hatası", "Ağ/İletişim hatası", "Yazılım/Firmware hatası",
        "Barkod/Okuyucu arızası", "WMS entegrasyon hatası", "PLC program hatası", "Diğer"
    ],
    "🏗️ Yapısal / İnşaat": [
        "Raf/Kafes yapı hasarı", "Zemin bozulması", "Kapı/Bariyer arızası",
        "Aydınlatma arızası", "Klima/Havalandırma arızası", "Diğer"
    ],
    "🔋 Enerji / Şarj": [
        "Şarj istasyonu arızası", "Akü değişimi gerekli", "Şarj kablosu hasarı",
        "Güç kaynağı sorunu", "Diğer"
    ],
    "🚒 Güvenlik / Emniyet": [
        "Yangın söndürme sistemi", "Sprinkler arızası", "Acil durdurma butonu",
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
    """Supabase secrets tanımlı mı kontrol et, değilse kullanıcıya açıklama göster."""
    try:
        _ = st.secrets["supabase"]["url"]
        _ = st.secrets["supabase"]["key"]
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
        url = f"{sb_url()}/rest/v1/{tablo}?{filtre}&order=id.desc" if filtre else \
              f"{sb_url()}/rest/v1/{tablo}?order=id.desc"
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

# ── Yardımcı: Supabase listesini DataFrame'e çevir ────────────────────────

def sb_to_df(rows: list, kolon_map: dict = None) -> pd.DataFrame:
    """Supabase JSON listesini Türkçe kolon adlı DataFrame'e çevirir."""
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    # Supabase sistem kolonlarını düşür
    df = df.drop(columns=[c for c in ["id","created_at"] if c in df.columns])
    if kolon_map:
        df = df.rename(columns=kolon_map)
    # Sayısal olması gereken kolonları dönüştür
    for col in ["Stok Miktarı","Kritik Seviye","Maksimum Stok","Son Fiyat (TL)",
                "Çözüm Süresi (Dk)","Malzeme Maliyeti (TL)","İş Gücü Maliyeti (TL)","Toplam Maliyet (TL)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

# ── Kolon eşleştirme haritaları ───────────────────────────────────────────

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

ARIZA_KOLON_MAP_TERS = {v: k for k, v in ARIZA_KOLON_MAP.items()}

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

# ── Supabase'den veri çekme fonksiyonları ─────────────────────────────────

@st.cache_data(ttl=30)
def ariza_df_getir() -> pd.DataFrame:
    try:
        rows = sb_select("ariza_kayitlari")
        return sb_to_df(rows, ARIZA_KOLON_MAP)
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=30)
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
def makine_listesi_getir() -> dict:
    """Supabase'den bölge bazlı makine listesini çek."""
    try:
        rows = sb_select("makine_listesi", "aktif=eq.true")
        if not rows:
            return None  # None → sabit listeye düş
        result = {}
        for r in rows:
            bolge = r.get("bolge", "")
            makine = r.get("makine_adi", "")
            if bolge and makine:
                result.setdefault(bolge, []).append(makine)
        return result if result else None
    except Exception:
        return None

@st.cache_data(ttl=60)
def ariza_turu_listesi_getir() -> dict:
    """Supabase'den arıza türü listesini çek."""
    try:
        rows = sb_select("ariza_turu_listesi", "aktif=eq.true")
        if not rows:
            return None  # None → sabit listeye düş
        result = {}
        for r in rows:
            kat = r.get("kategori", "")
            alt = r.get("alt_tur", "")
            if kat and alt:
                result.setdefault(kat, []).append(alt)
        return result if result else None
    except Exception:
        return None

def cache_temizle():
    ariza_df_getir.clear()
    stok_df_getir.clear()
    kullanicilar_getir.clear()
    makine_listesi_getir.clear()
    ariza_turu_listesi_getir.clear()

def aktif_makine_listesi() -> dict:
    """Supabase varsa oradan, yoksa sabit listeden döner."""
    db = makine_listesi_getir()
    return db if db else MAKINE_LISTESI_BOLGE

def aktif_ariza_turleri() -> dict:
    """Supabase varsa oradan, yoksa sabit listeden döner."""
    db = ariza_turu_listesi_getir()
    return db if db else ARIZA_TURLERI

# ── Veritabanı başlatma: tablolar boşsa varsayılan verileri yaz ───────────

def veritabani_hazirla():
    # Secrets yoksa veya URL boşsa çalışma
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        if not url or not url.startswith("http") or not key:
            return  # Sessizce çık, secrets_kontrol zaten uyarıyı gösterecek
    except Exception:
        return
    # Stok tablosu boşsa başlangıç verisi ekle
    mevcut_stok = sb_select("stok")
    if not mevcut_stok:
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

    # Kullanıcı tablosu boşsa varsayılan kullanıcıları ekle
    mevcut_kul = sb_select("kullanicilar")
    if not mevcut_kul:
        varsayilanlar = [
            {"kullanici_adi":"admin",    "sifre_hash":hashlib.sha256("1905".encode()).hexdigest(),"tam_ad":"Sistem Yöneticisi","rol":"Yönetici"},
            {"kullanici_adi":"sezer",    "sifre_hash":hashlib.sha256("1905".encode()).hexdigest(),"tam_ad":"Sezer Bey","rol":"Yönetici"},
            {"kullanici_adi":"teknik01", "sifre_hash":hashlib.sha256("1905".encode()).hexdigest(),"tam_ad":"Teknisyen 1","rol":"Teknisyen"},
            {"kullanici_adi":"uretim",   "sifre_hash":hashlib.sha256("1905".encode()).hexdigest(),"tam_ad":"Üretim Operatörü","rol":"Operatör"},
        ]
        for k in varsayilanlar:
            sb_insert("kullanicilar", k)

secrets_kontrol()
veritabani_hazirla()

# =============================================================================
# YARDIMCI FONKSİYONLAR
# =============================================================================

def log_yaz(islem: str, detay: str = ""):
    kullanici = st.session_state.get("aktif_kullanici", "Sistem")
    sb_insert("sistem_log", {
        "zaman":    datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "kullanici": kullanici,
        "islem":    islem,
        "detay":    detay
    })

def sla_hesapla(oncelik: str, acilis: str, kapanis: str = None) -> dict:
    sla_dk = ARIZA_ONCELIKLERI.get(oncelik, {}).get("sla_dk", 480)
    try:
        ac    = datetime.strptime(acilis, "%d/%m/%Y %H:%M")
        bitis = datetime.strptime(kapanis, "%d/%m/%Y %H:%M") if kapanis else datetime.now()
        gecen = (bitis - ac).total_seconds() / 60
        return {
            "gecen_dk": int(gecen),
            "sla_dk":   sla_dk,
            "oran":     round(gecen / sla_dk * 100, 1),
            "durum":    "✅ SLA İçinde" if gecen <= sla_dk else "⚠️ SLA Aşıldı"
        }
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
    except Exception:
        return KULLANICILAR_DEFAULT



# SAYFA KONFİGÜRASYONU & CSS
# =============================================================================

st.set_page_config(
    page_title="TeknikPro CMMS v2.0",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
/* ── Genel Temel ─────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    font-size: 14px;
}

/* ── Arka Plan ───────────────────────────────────────── */
.stApp {
    background: linear-gradient(160deg, #0f172a 0%, #1e293b 60%, #0f172a 100%) !important;
}

/* ── Sidebar ─────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0c1220 0%, #111827 100%) !important;
    border-right: 1px solid rgba(99,179,237,0.12) !important;
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 { color: #93c5fd !important; }

/* ── Metrik Kartlar ──────────────────────────────────── */
[data-testid="metric-container"] {
    background: rgba(30,41,59,0.8) !important;
    border: 1px solid rgba(99,179,237,0.18) !important;
    border-radius: 12px !important;
    padding: 16px 20px !important;
    backdrop-filter: blur(8px);
}
[data-testid="metric-container"] label {
    color: #94a3b8 !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-size: 28px !important;
    font-weight: 700 !important;
}
[data-testid="stMetricDelta"] { font-size: 12px !important; }

/* ── Başlıklar ───────────────────────────────────────── */
h1 { color: #e2e8f0 !important; font-weight: 700 !important; font-size: 26px !important; }
h2 { color: #cbd5e1 !important; font-weight: 600 !important; font-size: 20px !important; }
h3 { color: #94a3b8 !important; font-weight: 600 !important; font-size: 16px !important; }
p, span, li { color: #cbd5e1 !important; }
label { color: #94a3b8 !important; font-size: 13px !important; }

/* ── Tab Navigasyon ──────────────────────────────────── */
[data-testid="stTabs"] [role="tablist"] {
    background: rgba(15,23,42,0.6) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    border: 1px solid rgba(99,179,237,0.12) !important;
    gap: 2px !important;
}
[data-testid="stTabs"] [role="tab"] {
    color: #64748b !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    border-radius: 8px !important;
    padding: 8px 16px !important;
    transition: all 0.2s ease !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: rgba(59,130,246,0.2) !important;
    color: #93c5fd !important;
    border: 1px solid rgba(99,179,237,0.35) !important;
}

/* ── Form Elemanları ─────────────────────────────────── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] select,
.stSelectbox > div > div {
    background: rgba(15,23,42,0.9) !important;
    border: 1px solid rgba(99,179,237,0.2) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
    font-size: 14px !important;
    transition: border-color 0.2s ease !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: rgba(99,179,237,0.5) !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,0.12) !important;
}

/* ── Selectbox Dropdown Listesi ──────────────────────── */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background-color: #1e293b !important;
    color: #e2e8f0 !important;
}
[data-baseweb="popover"],
[data-baseweb="popover"] * {
    background-color: #1e293b !important;
    color: #e2e8f0 !important;
}
ul[role="listbox"] {
    background-color: #1e293b !important;
    border: 1px solid rgba(99,179,237,0.25) !important;
    border-radius: 8px !important;
}
li[role="option"] {
    background-color: #1e293b !important;
    color: #e2e8f0 !important;
}
li[role="option"]:hover,
li[role="option"][aria-selected="true"] {
    background-color: #2d4a6e !important;
    color: #ffffff !important;
}
[data-baseweb="menu"] {
    background-color: #1e293b !important;
    border: 1px solid rgba(99,179,237,0.25) !important;
    border-radius: 8px !important;
}
[data-baseweb="menu"] ul {
    background-color: #1e293b !important;
}
[data-baseweb="menu"] li {
    color: #e2e8f0 !important;
    background-color: #1e293b !important;
}
[data-baseweb="menu"] li:hover {
    background-color: #2d4a6e !important;
    color: #ffffff !important;
}
/* Seçili değer metni ────────────────────────────────── */
[data-testid="stSelectbox"] [data-baseweb="select"] span,
[data-testid="stSelectbox"] [data-baseweb="select"] div {
    color: #e2e8f0 !important;
    background-color: transparent !important;
}
/* Radio butonları ───────────────────────────────────── */
[data-testid="stRadio"] label {
    color: #cbd5e1 !important;
}
/* Number input ──────────────────────────────────────── */
[data-testid="stNumberInput"] div[data-baseweb="input"] {
    background-color: rgba(15,23,42,0.9) !important;
    border-color: rgba(99,179,237,0.2) !important;
}

/* ── Butonlar ────────────────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #1d4ed8, #2563eb) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 10px 20px !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.02em !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #1e40af, #1d4ed8) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(29,78,216,0.35) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* ── Form Gönder Butonu ──────────────────────────────── */
[data-testid="stFormSubmitButton"] > button {
    background: linear-gradient(135deg, #059669, #10b981) !important;
    width: 100% !important;
    padding: 12px 24px !important;
    font-size: 14px !important;
    font-weight: 700 !important;
    border-radius: 10px !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    background: linear-gradient(135deg, #047857, #059669) !important;
    box-shadow: 0 4px 16px rgba(5,150,105,0.35) !important;
}

/* ── Download Butonu ─────────────────────────────────── */
[data-testid="stDownloadButton"] > button {
    background: rgba(30,41,59,0.8) !important;
    border: 1px solid rgba(99,179,237,0.25) !important;
    color: #93c5fd !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    border-radius: 8px !important;
}
[data-testid="stDownloadButton"] > button:hover {
    border-color: rgba(99,179,237,0.5) !important;
    background: rgba(30,41,59,1) !important;
}

/* ── Dataframe ───────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(99,179,237,0.12) !important;
    border-radius: 12px !important;
    overflow: hidden;
}
[data-testid="stDataFrame"] iframe {
    border-radius: 12px !important;
}

/* ── Bildirimler ─────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border-left-width: 4px !important;
    font-size: 13px !important;
}

/* ── Expander ────────────────────────────────────────── */
[data-testid="stExpander"] {
    background: rgba(30,41,59,0.5) !important;
    border: 1px solid rgba(99,179,237,0.12) !important;
    border-radius: 10px !important;
}
[data-testid="stExpander"] summary {
    color: #93c5fd !important;
    font-weight: 600 !important;
    font-size: 13px !important;
}

/* ── Number Input ────────────────────────────────────── */
[data-testid="stNumberInput"] input {
    background: rgba(15,23,42,0.9) !important;
    border: 1px solid rgba(99,179,237,0.2) !important;
    border-radius: 8px !important;
    color: #e2e8f0 !important;
}

/* ── Çizgi ───────────────────────────────────────────── */
hr { border-color: rgba(99,179,237,0.1) !important; }

/* ── Özel Kart Bileşenleri ───────────────────────────── */
.durum-karti {
    background: rgba(30,41,59,0.7);
    border: 1px solid rgba(99,179,237,0.15);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
    backdrop-filter: blur(4px);
    transition: border-color 0.2s ease;
}
.durum-karti:hover {
    border-color: rgba(99,179,237,0.35);
}
.kritik-banner {
    background: linear-gradient(135deg, rgba(220,38,38,0.15), rgba(153,27,27,0.1));
    border: 1px solid rgba(220,38,38,0.4);
    border-left: 4px solid #dc2626;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 8px 0 16px 0;
}
.sla-badge {
    display: inline-block;
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.04em;
}
.sla-ok   { background: rgba(22,163,74,0.15);  border:1px solid rgba(22,163,74,0.4);  color:#4ade80; }
.sla-warn { background: rgba(220,38,38,0.15);  border:1px solid rgba(220,38,38,0.4);  color:#f87171; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# YETKİLENDİRME SİSTEMİ
# =============================================================================

def sidebar_giris():
    """Sidebar'da oturum yönetimi"""
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
                        st.session_state.oturum_acik      = True
                        st.session_state.aktif_kullanici  = k
                        st.session_state.aktif_tam_ad     = kullanicilar[k]["tam_ad"]
                        st.session_state.aktif_rol        = kullanicilar[k]["rol"]
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
              <div style="font-size:11px;color:#64748b;font-weight:600;text-transform:uppercase;
                          letter-spacing:0.06em;margin-bottom:6px;">AKTİF OTURUM</div>
              <div style="font-size:15px;color:#e2e8f0;font-weight:600;">👤 {tam_ad}</div>
              <div style="font-size:12px;color:#93c5fd;margin-top:4px;">🏷️ {rol}</div>
              <div style="font-size:11px;color:#475569;margin-top:6px;">
                {datetime.now().strftime("%d %b %Y — %H:%M")}
              </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🚪 Çıkış Yap", use_container_width=True):
                log_yaz("ÇIKIŞ", f"{tam_ad} sistemden çıktı")
                for k in ["oturum_acik","aktif_kullanici","aktif_tam_ad","aktif_rol"]:
                    st.session_state.pop(k, None)
                st.rerun()

def yetkili_mi(min_rol: str = "Operatör") -> bool:
    """Rol hiyerarşisi: Yönetici > Teknisyen > Operatör"""
    ROL_SIRASI = {"Yönetici": 3, "Teknisyen": 2, "Operatör": 1}
    kullanici_rol = st.session_state.get("aktif_rol", "")
    return ROL_SIRASI.get(kullanici_rol, 0) >= ROL_SIRASI.get(min_rol, 99)

def giris_gerektir(min_rol: str = "Teknisyen") -> bool:
    if not st.session_state.get("oturum_acik", False):
        st.markdown("""
        <div style="text-align:center;padding:60px 20px;">
          <div style="font-size:48px;margin-bottom:16px;">🔒</div>
          <div style="font-size:18px;color:#94a3b8;font-weight:600;">Bu bölüme erişmek için giriş yapın</div>
          <div style="font-size:13px;color:#64748b;margin-top:8px;">
            Sol paneldeki giriş formunu kullanın
          </div>
        </div>
        """, unsafe_allow_html=True)
        return False
    if not yetkili_mi(min_rol):
        st.error(f"⛔ Bu işlem için **{min_rol}** yetkisi gereklidir. Mevcut rolünüz: {st.session_state.aktif_rol}")
        return False
    return True


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("""
    <div style="padding:20px 8px 8px;">
      <div style="font-size:10px;font-weight:700;letter-spacing:0.12em;
                  text-transform:uppercase;color:#3b82f6;margin-bottom:4px;">
        ENTERPRISE CMMS
      </div>
      <div style="font-size:20px;font-weight:800;color:#e2e8f0;line-height:1.2;">
        TeknikPro<br>
        <span style="color:#3b82f6;">v2.0</span>
      </div>
      <div style="font-size:11px;color:#475569;margin-top:6px;">
        TPM & Arıza Yönetim Platformu
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Canlı sayaçlar
    try:
        df_sb = ariza_df_getir()
        if not df_sb.empty and "Durum" in df_sb.columns:
            acik   = len(df_sb[df_sb["Durum"] == "Açık"])
            kritik = len(df_sb[(df_sb["Durum"]=="Açık") & (df_sb["Öncelik"].str.startswith("🔴", na=False))])
        else:
            acik, kritik = 0, 0
        st.markdown(f"""
        <div style="display:flex;gap:8px;margin:16px 8px 8px;">
          <div style="flex:1;background:rgba(220,38,38,0.1);border:1px solid rgba(220,38,38,0.3);
                      border-radius:8px;padding:10px 12px;text-align:center;">
            <div style="font-size:22px;font-weight:700;color:#f87171;">{kritik}</div>
            <div style="font-size:10px;color:#94a3b8;font-weight:600;margin-top:2px;">KRİTİK</div>
          </div>
          <div style="flex:1;background:rgba(234,88,12,0.1);border:1px solid rgba(234,88,12,0.3);
                      border-radius:8px;padding:10px 12px;text-align:center;">
            <div style="font-size:22px;font-weight:700;color:#fb923c;">{acik}</div>
            <div style="font-size:10px;color:#94a3b8;font-weight:600;margin-top:2px;">AÇIK</div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    except:
        pass

    st.markdown("---")
    st.markdown("<div style='font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#475569;padding-left:4px;margin-bottom:8px;'>HIZLI BİLGİ</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-size:12px;color:#64748b;padding-left:4px;line-height:1.8;">
      📅 {datetime.now().strftime("%A, %d %B %Y")}<br>
      🏭 Tesis: Adana LM<br>
      📋 Sistem: CMMS v2.0
    </div>
    """, unsafe_allow_html=True)
    components.html("""
    <div style="font-size:12px;color:#64748b;padding-left:4px;margin-top:-6px;">
      🕐 <span id="saat" style="color:#64748b;">--:--:--</span> (Türkiye)
    </div>
    <script>
      function tick() {
        var now = new Date();
        var h = String(now.getHours()).padStart(2,'0');
        var m = String(now.getMinutes()).padStart(2,'0');
        var s = String(now.getSeconds()).padStart(2,'0');
        var el = document.getElementById('saat');
        if (el) el.textContent = h + ':' + m + ':' + s;
      }
      tick();
      setInterval(tick, 1000);
    </script>
    """, height=28)

sidebar_giris()

# =============================================================================
# ANA BAŞLIK
# =============================================================================

st.markdown("""
<div style="margin-bottom:24px;">
  <h1 style="margin:0;padding:0;">🛡️ Teknik Bakım & Arıza Yönetim Sistemi</h1>
  <p style="color:#475569;font-size:13px;margin-top:4px;">
    Computerized Maintenance Management System — Endüstriyel TPM Platformu
  </p>
</div>
""", unsafe_allow_html=True)

# =============================================================================
# SEKMELER
# =============================================================================

tab_pano, tab_yeni, tab_kapat, tab_rapor, tab_stok, tab_ayar = st.tabs([
    "📊 Canlı Pano",
    "➕ Yeni Talep Aç",
    "✅ Talep Kapat",
    "📋 Raporlama & Arşiv",
    "📦 Stok Yönetimi",
    "⚙️ Sistem Ayarları"
])


# =============================================================================
# SEKME 1: CANLI PANO
# =============================================================================

with tab_pano:
    df = ariza_df_getir()

    if df.empty or "Durum" not in df.columns:
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1: st.metric("Toplam Talep", 0)
        with col2: st.metric("Acik Talepler", 0)
        with col3: st.metric("Kapatilan", 0)
        with col4: st.metric("Kritik Acik", 0)
        with col5: st.metric("SLA Asimi", 0)
        st.markdown("---")
        st.info("Sistemde henuz kayit bulunmuyor. Yeni Talep Ac sekmesinden ilk arizayi ekleyin.")
    else:
        toplam   = len(df)
        acik     = len(df[df["Durum"] == "Açık"])
        kapali   = len(df[df["Durum"] == "Kapalı"])
        kritik   = len(df[(df["Durum"] == "Açık") & (df["Öncelik"].str.startswith("🔴", na=False))])
        sla_asan = len(df[df["SLA Durumu"].str.contains("Aşıldı", na=False)])

        col1, col2, col3, col4, col5 = st.columns(5)
        bugun = datetime.now().strftime("%d/%m/%Y")
        bugun_sayi = len(df[df["Açılış Tarihi"].str.startswith(bugun, na=False)]) if "Açılış Tarihi" in df.columns else 0
        with col1: st.metric("Toplam Talep", toplam, delta=f"+{bugun_sayi} bugun")
        with col2: st.metric("Acik Talepler", acik)
        with col3: st.metric("Kapatilan", kapali, delta=f"Kapatma orani: %{round(kapali/max(toplam,1)*100)}")
        with col4: st.metric("Kritik Acik", kritik, delta="acil mudahale" if kritik > 0 else "Temiz")
        with col5: st.metric("SLA Asimi", sla_asan)

        st.markdown("---")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("#### Oncelik Bazli Acik Talepler")
            if acik > 0:
                acik_df2 = df[df["Durum"] == "Açık"]
                onc_say = acik_df2["Öncelik"].value_counts()
                onc_say.index = [i[:30] for i in onc_say.index]
                st.bar_chart(onc_say, height=260)
            else:
                st.info("Acik talep yok")
        with col_g2:
            st.markdown("#### Makine Bazli Ariza Sayisi")
            mak_say = df["Makine"].value_counts().head(8)
            st.bar_chart(mak_say, height=260)

        st.markdown("#### 30 Gunluk Ariza Trendi")
        try:
            df_trend = df.copy()
            df_trend["Tarih"] = pd.to_datetime(
                df_trend["Açılış Tarihi"], format="%d/%m/%Y %H:%M", errors="coerce"
            ).dt.date
            son_30 = date.today() - timedelta(days=30)
            df_trend = df_trend[df_trend["Tarih"] >= son_30]
            gunluk = df_trend.groupby("Tarih").size().rename("Arıza Sayısı")
            if len(gunluk) > 0:
                st.line_chart(gunluk, height=200)
        except Exception as e:
            st.caption(f"Trend verisi islenemedi: {e}")

        st.markdown("---")
        st.markdown("#### Mudahale Bekleyen Acik Talepler")
        acik_df = df[df["Durum"] == "Açık"].copy()
        if acik_df.empty:
            st.success("🎉 Müdahale bekleyen açık talep bulunmuyor. Harika iş!")
        else:
            k_df = acik_df[acik_df["Öncelik"].str.startswith("🔴", na=False)]
            if not k_df.empty:
                st.error(f"KRITIK: {len(k_df)} adet URETIM DURDURUCU ariza! Makine(ler): {', '.join(k_df['Makine'].unique()[:3])}")
            goster = ["Talep No","Öncelik","Açılış Tarihi","Bildiren","Makine","Arıza Türü","Arıza Tanımı","SLA Durumu"]
            goster = [s for s in goster if s in acik_df.columns]
            st.dataframe(acik_df[goster], use_container_width=True, hide_index=True)


        with tab_yeni:
            pass


with tab_yeni:
    st.markdown("### ➕ Yeni Arıza Bildirimi Oluştur")
    st.caption("Bu form tüm personele açıktır. Oturum açmadan da kullanılabilir.")

    if not st.session_state.get("_talep_gonderildi", False):
        st.session_state["bildirim_saat_default"] = datetime.now().strftime("%H:%M")
    else:
        st.session_state["_talep_gonderildi"] = False

    # Bölge seçimi form dışında — makine listesini dinamik günceller
    secili_bolge = st.selectbox(
        "🏭 Tesis / Bölge Seçin *",
        BOLGELER,
        help="Arızanın gerçekleştiği tesisi seçin"
    )

    with st.form("yeni_talep_formu", clear_on_submit=True):
        st.markdown("#### 👤 Bildiren Personel Bilgileri")
        col_b1, col_b2, col_b3 = st.columns(3)
        with col_b1:
            bildiren      = st.text_input("Ad Soyad *", placeholder="Ahmet Yıldız")
        with col_b2:
            bildiren_dept = st.selectbox("Departman *", [
                "Üretim", "Depo", "Lojistik", "Bakım", "Kalite", "İdari", "Diğer"
            ])
        with col_b3:
            vardiya = st.selectbox("Vardiya *", [
                "Gündüz (08:00–16:00)", "Akşam (16:00–00:00)", "Gece (00:00–08:00)"
            ])

        st.markdown(f"#### 🏭 Arıza Lokasyonu & Tipi — {secili_bolge}")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            makine    = st.selectbox("Makine / Sistem *", aktif_makine_listesi().get(secili_bolge, ["Diğer"]))
            ariza_tur = st.selectbox("Arıza Kategorisi *", list(aktif_ariza_turleri().keys()))
        with col_m2:
            oncelik       = st.selectbox("Kritiklik Seviyesi (SLA) *", list(ARIZA_ONCELIKLERI.keys()))
            bildirim_saat = st.text_input(
                "Arıza Fark Edilme Saati",
                value=st.session_state.get("bildirim_saat_default", datetime.now().strftime("%H:%M")),
                help="SS:DD formatında (örn: 14:30)"
            )

        alt_kategori = st.selectbox(
            "Alt Kategori",
            aktif_ariza_turleri().get(ariza_tur, ["Diğer"]),
            help="Arıza tipini daha spesifik tanımlayın"
        )
        ariza_tanimi = st.text_area(
            "Arıza Tanımı *",
            placeholder="Arızanın belirti ve etkilerini kısaca açıklayın...",
            height=100
        )
        foto_notu = st.text_input(
            "Fotoğraf / Referans Notu",
            placeholder="Fotoğraf çekildiyse referans kodu veya açıklama girin"
        )

        sla_bilgi = ARIZA_ONCELIKLERI[oncelik]
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.6);border:1px solid rgba(99,179,237,0.15);
                    border-radius:8px;padding:12px 16px;margin:8px 0;font-size:12px;">
          🏭 <strong style="color:#93c5fd;">Bölge:</strong>
          <span style="color:#fbbf24;"> {secili_bolge}</span>
          &nbsp;&nbsp;|&nbsp;&nbsp;
          ⏱ <strong style="color:#93c5fd;">SLA Hedefi:</strong>
          <span style="color:#cbd5e1;"> <strong style="color:#fbbf24;">{sla_bilgi["sla_dk"]} dakika</strong></span>
        </div>
        """, unsafe_allow_html=True)

        submit_yeni = st.form_submit_button("🚀 Arıza Talebi Oluştur", use_container_width=True)

        if submit_yeni:
            if not bildiren.strip():
                st.error("❌ 'Ad Soyad' alanı zorunludur.")
            elif not ariza_tanimi.strip():
                st.error("❌ 'Arıza Tanımı' alanı zorunludur.")
            else:
                no = talep_no_uret()
                yeni_sb = {
                    "talep_no": no, "bolge": secili_bolge,
                    "durum": "Açık", "oncelik": oncelik,
                    "vardiya": vardiya,
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
                    "malzeme_maliyeti": 0, "isguc_maliyeti": 0,
                    "toplam_maliyet": 0, "fotograf_notu": foto_notu,
                    "kapatma_onayi": ""
                }
                sb_insert("ariza_kayitlari", yeni_sb)
                cache_temizle()
                st.session_state["_talep_gonderildi"] = True
                log_yaz("YENİ TALEP", f"{no} — {secili_bolge} — {makine} — {bildiren}")
                st.success(f"✅ Talep **{no}** oluşturuldu! Bölge: {secili_bolge} | SLA: {sla_bilgi['sla_dk']} dk")
                time.sleep(1)
                st.rerun()


with tab_kapat:
    if not giris_gerektir("Teknisyen"):
        pass
    else:
        df_k = ariza_df_getir()

        if df_k.empty or "Durum" not in df_k.columns:
            st.success("🎉 Müdahale bekleyen açık talep bulunmuyor. Harika iş!")
        else:
            acik_k = df_k[df_k["Durum"] == "Açık"].copy()

            if acik_k.empty:
                st.success("🎉 Müdahale bekleyen açık talep bulunmuyor. Harika iş!")
            else:
                bolge_secim_k = st.selectbox(
                    "🏭 Bölge Filtresi",
                    ["Tüm Bölgeler"] + BOLGELER,
                    key="kapat_bolge"
                )
                if bolge_secim_k != "Tüm Bölgeler" and "Bölge" in acik_k.columns:
                    acik_k = acik_k[acik_k["Bölge"] == bolge_secim_k]

                if acik_k.empty:
                    st.info(f"ℹ️ {bolge_secim_k} bölgesinde açık talep bulunmuyor.")
                else:
                    krit_k = acik_k[acik_k["Öncelik"].str.startswith("🔴", na=False)]
                    if not krit_k.empty:
                        st.markdown(f'''<div class="kritik-banner"><strong style="color:#f87171;">🚨 {len(krit_k)} KRİTİK ARIZA</strong><span style="color:#94a3b8;font-size:12px;"> — Acil müdahale bekliyor</span></div>''', unsafe_allow_html=True)

                    col_s1, _ = st.columns([3, 1])
                    with col_s1:
                        secenekler = acik_k.apply(
                            lambda r: f"[{r['Talep No']}] {str(r.get('Öncelik',''))[:2]} {r.get('Makine','')} - {str(r.get('Arıza Tanımı',''))[:60]}",
                            axis=1
                        ).tolist()
                        secilen = st.selectbox("📋 Kapatılacak Talebi Seçin", secenekler)

                    secilen_no = secilen.split("]")[0].replace("[","").strip()
                    talep_df = df_k[df_k["Talep No"] == secilen_no]
                    if talep_df.empty:
                        st.error("Talep bulunamadi.")
                        st.stop()
                    talep = talep_df.iloc[0]

                    sla_bilgi_g = sla_hesapla(
                        talep.get("Öncelik", ""),
                        talep.get("Açılış Tarihi", "")
                    )
                    st.info(
                        f"Talep: {talep.get('Talep No','')} | "
                        f"Makine: {talep.get('Makine','')} | "
                        f"Acilis: {talep.get('Acilis Tarihi','')} | "
                        f"Gecen: {sla_bilgi_g.get('gecen_dk',0)} dk | "
                        f"{sla_bilgi_g.get('durum','')}"
                    )

                    def mttr_mtbf_hesapla(makine_adi):
                        try:
                            df_all = ariza_df_getir()
                            if df_all.empty or "Durum" not in df_all.columns:
                                return None
                            df_m = df_all[
                                (df_all["Makine"] == makine_adi) &
                                (df_all["Durum"]  == "Kapalı") &
                                (df_all["Çözüm Süresi (Dk)"].notna()) &
                                (df_all["Çözüm Süresi (Dk)"] != "")
                            ].copy()
                            if df_m.empty:
                                return None
                            df_m["sure"] = pd.to_numeric(df_m["Çözüm Süresi (Dk)"], errors="coerce")
                            mttr = round(df_m["sure"].mean(), 1)
                            df_m["kap"] = pd.to_datetime(df_m["Kapatma Tarihi"], format="%d/%m/%Y %H:%M", errors="coerce")
                            df_m = df_m.dropna(subset=["kap"]).sort_values("kap")
                            mtbf_dk = None
                            if len(df_m) >= 2:
                                farklar = df_m["kap"].diff().dropna()
                                mtbf_dk = round(farklar.dt.total_seconds().mean() / 60, 1)
                            return {"mttr": mttr, "mtbf": mtbf_dk, "toplam_ariza": len(df_m)}
                        except:
                            return None

                    ISCI_SAAT_UCRETI = 300

                    st.markdown("#### 🔧 Müdahale & Çözüm Bilgileri")
                    with st.form("kapat_formu"):
                        st.markdown("##### 👤 Teknisyen & Zaman")
                        col_k1, col_k2, col_k3 = st.columns(3)
                        with col_k1:
                            mudahale_eden = st.text_input(
                                "Müdahale Eden Teknisyen *",
                                value=st.session_state.get("aktif_tam_ad", "")
                            )
                        with col_k2:
                            mudahale_bas_str = st.text_input(
                                "🕐 Müdahaleye Başlama Saati *",
                                value=datetime.now().strftime("%H:%M"),
                                help="SS:DD formatinda (ornek: 14:30)"
                            )
                        with col_k3:
                            mudahale_bit_str = st.text_input(
                                "🕑 Arıza Giderilme Saati *",
                                value=datetime.now().strftime("%H:%M"),
                                help="SS:DD formatinda (ornek: 14:30)"
                            )

                        try:
                            bas_dt = datetime.strptime(date.today().strftime("%d/%m/%Y") + " " + mudahale_bas_str.strip(), "%d/%m/%Y %H:%M")
                            bit_dt = datetime.strptime(date.today().strftime("%d/%m/%Y") + " " + mudahale_bit_str.strip(), "%d/%m/%Y %H:%M")
                            if bit_dt < bas_dt:
                                bit_dt += timedelta(days=1)
                            cozum_suresi_dk = max(1, int((bit_dt - bas_dt).total_seconds() / 60))
                            saat_parse_ok = True
                        except ValueError:
                            cozum_suresi_dk = 1
                            saat_parse_ok = False

                        isguc_maliyet = round((cozum_suresi_dk / 60) * ISCI_SAAT_UCRETI, 2)

                        if not saat_parse_ok:
                            st.warning("⚠️ Saat formatı hatalı. SS:DD formatında girin (örn: 14:30)")
                        else:
                            st.info(
                                f"Cozum Suresi: {cozum_suresi_dk} dakika "
                                f"({cozum_suresi_dk//60}s {cozum_suresi_dk%60}dk)  |  "
                                f"Is Gucu Maliyeti: {isguc_maliyet:,.0f} TL "
                                f"(300 TL/saat x {cozum_suresi_dk/60:.2f} saat)"
                            )

                        st.markdown("##### 📝 Çözüm & Analiz")
                        col_k4, col_k5 = st.columns(2)
                        with col_k4:
                            kok_neden = st.selectbox("Kök Neden Kategorisi", [
                                "Yağlama eksikliği", "Aşınma (ömür tükenmesi)", "Hatalı kullanım",
                                "Yetersiz bakım periyodu", "Tasarım/malzeme yetersizliği",
                                "Dış etken (toz, nem, darbe)", "Yazılım/donanım arızası", "Bilinmiyor", "Diğer"
                            ])
                        with col_k5:
                            kapatma_onayi = st.selectbox("Kapatma Onayı", [
                                "Teknisyen Onayı", "Vardiya Amiri Onayı", "Bakım Müdürü Onayı"
                            ])

                        cozum_aciklama = st.text_area("Uygulanan Çözüm & Teknik Notlar *", height=90)
                        neden_analizi  = st.text_area("5 Neden Analizi", height=100)
                        kaizen         = st.text_area("Kaizen / İyileştirme Önerisi", height=70)

                        st.markdown("##### 📦 Kullanılan Malzeme")
                        df_stok_k = stok_df_getir()
                        stok_secenekler = ["—  Malzeme Kullanılmadı"]
                        if not df_stok_k.empty and "Malzeme Adı" in df_stok_k.columns:
                            stok_secenekler += df_stok_k["Malzeme Adı"].tolist()

                        col_stk1, col_stk2, col_stk3 = st.columns(3)
                        with col_stk1:
                            malzeme_secim = st.selectbox("Stoktan Malzeme", stok_secenekler)
                        with col_stk2:
                            malzeme_adet = st.number_input("Kullanılan Miktar", min_value=0, step=1, value=0)
                        with col_stk3:
                            malzeme_maliyet = st.number_input("Malzeme Maliyeti (TL)", min_value=0, step=50, value=0)

                        submit_kapat = st.form_submit_button("✅ Talebi Kapat & Kaydet", use_container_width=True)

                        if submit_kapat:
                            if not mudahale_eden.strip():
                                st.error("❌ Teknisyen adı zorunludur.")
                            elif not saat_parse_ok:
                                st.error("❌ Saat formatı hatalı. SS:DD formatında girin (örn: 14:30)")
                            elif not cozum_aciklama.strip():
                                st.error("❌ Çözüm açıklaması zorunludur.")
                            else:
                                malzeme_metni = "-"
                                if "Kullanılmadı" not in malzeme_secim and malzeme_adet > 0:
                                    if not df_stok_k.empty and "Malzeme Adı" in df_stok_k.columns:
                                        stok_satirlar = df_stok_k[df_stok_k["Malzeme Adı"] == malzeme_secim]
                                        if not stok_satirlar.empty:
                                            stok_mik = int(stok_satirlar["Stok Miktarı"].values[0])
                                            if stok_mik < malzeme_adet:
                                                st.error(f"❌ Yetersiz stok! Mevcut: {stok_mik} adet")
                                                st.stop()
                                            yeni_stok = stok_mik - malzeme_adet
                                            sb_update("stok", f"malzeme_adi=eq.{malzeme_secim}", {
                                                "stok_miktari": yeni_stok,
                                                "son_guncelleme": datetime.now().strftime("%d/%m/%Y")
                                            })
                                    malzeme_metni = f"{malzeme_secim} x {malzeme_adet}"

                                toplam_maliyet = isguc_maliyet + malzeme_maliyet
                                kapatma_zaman  = datetime.now().strftime("%d/%m/%Y %H:%M")
                                mudahale_aralik = f"{mudahale_bas_str.strip()} - {mudahale_bit_str.strip()}"
                                sla_s = sla_hesapla(talep.get("Öncelik",""), talep.get("Açılış Tarihi",""), kapatma_zaman)

                                sb_update("ariza_kayitlari", f"talep_no=eq.{secilen_no}", {
                                    "durum":               "Kapalı",
                                    "kapatma_tarihi":      kapatma_zaman,
                                    "mudahale_eden":       mudahale_eden.strip(),
                                    "ilk_mudahale_saati":  mudahale_aralik,
                                    "cozum_suresi_dk":     int(cozum_suresi_dk),
                                    "sla_durumu":          sla_s["durum"],
                                    "cozum_aciklamasi":    cozum_aciklama.strip(),
                                    "kok_neden":           str(kok_neden),
                                    "bes_neden_analizi":   neden_analizi,
                                    "kaizen_onerisi":      kaizen,
                                    "kullanilan_malzemeler": malzeme_metni,
                                    "malzeme_maliyeti":    float(malzeme_maliyet),
                                    "isguc_maliyeti":      float(isguc_maliyet),
                                    "toplam_maliyet":      float(toplam_maliyet),
                                    "kapatma_onayi":       str(kapatma_onayi),
                                })
                                cache_temizle()
                                log_yaz("TALEP KAPATILDI",
                                    f"{secilen_no} - {mudahale_eden} - {cozum_suresi_dk} dk - {toplam_maliyet:.0f} TL")
                                st.success(
                                    f"Talep {secilen_no} basariyla kapatildi! "
                                    f"Sure: {cozum_suresi_dk} dk | "
                                    f"Is Gucu: {isguc_maliyet:,.0f} TL | "
                                    f"Toplam: {toplam_maliyet:,.0f} TL | "
                                    f"{sla_s['durum']}"
                                )
                                time.sleep(1.5)
                                st.rerun()

                    st.markdown("---")
                    st.markdown(f"#### MTTR ve MTBF Analizi - {talep.get('Makine','')}")
                    sonuc = mttr_mtbf_hesapla(talep.get("Makine",""))
                    if sonuc:
                        col_m1, col_m2, col_m3 = st.columns(3)
                        with col_m1:
                            st.metric("⏱ MTTR (Ort. Tamir Süresi)", f"{sonuc['mttr']} dk")
                        with col_m2:
                            st.metric("🔄 MTBF (Ort. Arızalar Arası)", f"{sonuc['mtbf']} dk" if sonuc["mtbf"] else "Yetersiz veri")
                        with col_m3:
                            st.metric("📊 Toplam Arıza", f"{sonuc['toplam_ariza']} adet")
                        if sonuc["mtbf"]:
                            avail = round(sonuc["mtbf"] / (sonuc["mtbf"] + sonuc["mttr"]) * 100, 1)
                            st.success(f"📈 Ekipman Kullanılabilirlik Oranı (Availability): %{avail} = MTBF / (MTBF + MTTR)")
                    else:
                        st.info("ℹ️ Yeterli kapatılmış arıza verisi yok. MTTR/MTBF hesaplanamadı.")


with tab_rapor:
    if not giris_gerektir("Teknisyen"):
        pass
    else:
        st.markdown("### 📋 Arıza Arşivi & Gelişmiş Raporlama")
        df_r = ariza_df_getir()

        # ── Filtreler ──────────────────────────────────────────────────
        with st.expander("🔍 Filtrele & Ara", expanded=True):
            col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
            with col_f1:
                f_bolge   = st.selectbox("Bölge",      ["Tümü"] + BOLGELER)
            with col_f2:
                f_durum   = st.selectbox("Durum",    ["Tümü", "Açık", "Kapalı"])
            with col_f3:
                f_oncelik = st.selectbox("Öncelik",  ["Tümü"] + list(ARIZA_ONCELIKLERI.keys()))
            with col_f4:
                f_makine  = st.selectbox("Makine", ["Tümü"] + sorted(set(
                    m for bl in aktif_makine_listesi().values() for m in bl
                )))
            with col_f5:
                f_tur     = st.selectbox("Arıza Türü", ["Tümü"] + list(aktif_ariza_turleri().keys()))

            col_t1, col_t2, col_t3 = st.columns([2,2,2])
            with col_t1:
                f_bas = st.date_input("Başlangıç", date(2025,1,1))
            with col_t2:
                f_bit = st.date_input("Bitiş",     date.today())
            with col_t3:
                f_arama = st.text_input("🔍 Metin Ara", placeholder="Talep no, personel, makine...")

        # Filtre uygula
        goster = df_r.copy()
        if goster.empty or "Durum" not in goster.columns:
            st.info("📭 Henüz arıza kaydı bulunmuyor. İlk talebi 'Yeni Talep Aç' sekmesinden ekleyin.")
        else:
            if f_bolge   != "Tümü" and "Bölge"      in goster.columns: goster = goster[goster["Bölge"]      == f_bolge]
            if f_durum   != "Tümü" and "Durum"       in goster.columns: goster = goster[goster["Durum"]       == f_durum]
            if f_oncelik != "Tümü" and "Öncelik"     in goster.columns: goster = goster[goster["Öncelik"]     == f_oncelik]
            if f_makine  != "Tümü" and "Makine"      in goster.columns: goster = goster[goster["Makine"]      == f_makine]
            if f_tur     != "Tümü" and "Arıza Türü"  in goster.columns: goster = goster[goster["Arıza Türü"]  == f_tur]

            if f_arama.strip():
                try:
                    mask = goster.apply(lambda r: r.astype(str).str.contains(f_arama, case=False, na=False).any(), axis=1)
                    goster = goster[mask]
                except: pass

            try:
                if "Açılış Tarihi" in goster.columns:
                    goster["_tarih"] = pd.to_datetime(goster["Açılış Tarihi"], format="%d/%m/%Y %H:%M", errors="coerce").dt.date
                    goster = goster[(goster["_tarih"] >= f_bas) & (goster["_tarih"] <= f_bit)].drop(columns=["_tarih"])
            except: pass

            # Özet metrikler
            col_oz1, col_oz2, col_oz3, col_oz4 = st.columns(4)
            with col_oz1: st.metric("Kayıt Sayısı", len(goster))
            with col_oz2:
                try:    ort_sure = round(pd.to_numeric(goster["Çözüm Süresi (Dk)"], errors="coerce").dropna().mean())
                except: ort_sure = "—"
                st.metric("Ort. Çözüm Süresi", f"{ort_sure} dk" if isinstance(ort_sure, (int,float)) else "—")
            with col_oz3:
                try:    toplam_mal = pd.to_numeric(goster["Toplam Maliyet (TL)"], errors="coerce").sum()
                except: toplam_mal = 0
                st.metric("Toplam Maliyet", f"{toplam_mal:,.0f} ₺")
            with col_oz4:
                try:    sla_asan_r = len(goster[goster["SLA Durumu"].str.contains("Aşıldı", na=False)])
                except: sla_asan_r = 0
                st.metric("SLA Aşımı", sla_asan_r)

            # İndir
            col_dl1, col_dl2 = st.columns([1,4])
            with col_dl1:
                csv_b = goster.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                st.download_button(
                    "📥 CSV İndir", csv_b,
                    file_name=f"ariza_raporu_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv", use_container_width=True
                )

            if not goster.empty:
                try:
                    st.dataframe(
                        goster.sort_values("Açılış Tarihi", ascending=False),
                        use_container_width=True, hide_index=True
                    )
                except:
                    st.dataframe(goster, use_container_width=True, hide_index=True)

            # Seçili talebin tam detayı
            if len(goster) > 0 and "Talep No" in goster.columns:
                with st.expander("📄 Talep Detay Görüntüle"):
                    secim_no = st.selectbox("Talep seçin", goster["Talep No"].tolist())
                    secim_satir = goster[goster["Talep No"] == secim_no]
                    if not secim_satir.empty:
                        s = secim_satir.iloc[0]
                        col_d1, col_d2 = st.columns(2)
                        alanlar = [a for a in ARIZA_SUTUNLARI if a in s.index]
                        yari = len(alanlar) // 2
                        with col_d1:
                            for alan in alanlar[:yari]:
                                if str(s[alan]) not in ["", "nan", "0", "0.0"]:
                                    st.markdown(f"**{alan}:** {s[alan]}")
                        with col_d2:
                            for alan in alanlar[yari:]:
                                if str(s[alan]) not in ["", "nan", "0", "0.0"]:
                                    st.markdown(f"**{alan}:** {s[alan]}")


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
            st.stop()

        # Bölge filtresi
        col_bolge_st, _ = st.columns([2, 4])
        with col_bolge_st:
            bolge_stok = st.selectbox(
                "🏭 Bölge Filtresi",
                ["Tüm Bölgeler"] + BOLGELER,
                key="stok_bolge"
            )

        # Bölge kolonu varsa filtrele
        if bolge_stok != "Tüm Bölgeler" and "Bölge" in df_st.columns:
            df_st_filtre = df_st[df_st["Bölge"] == bolge_stok].copy()
        else:
            df_st_filtre = df_st.copy()

        # Kritik stok alarmları
        kritik_stok = df_st_filtre[df_st_filtre["Stok Miktarı"] <= df_st_filtre["Kritik Seviye"]]
        if not kritik_stok.empty:
            for _, row in kritik_stok.iterrows():
                st.markdown(f"""
                <div class="kritik-banner">
                  ⚠️ <strong style="color:#fbbf24;">ACİL SİPARİŞ GEREKLİ:</strong>
                  <span style="color:#cbd5e1;"> {row['Malzeme Adı']}</span>
                  <span style="color:#94a3b8;font-size:12px;">
                    — Mevcut: <strong style="color:#f87171;">{row['Stok Miktarı']} {row.get('Birim','adet')}</strong>
                    / Kritik Seviye: {row['Kritik Seviye']}
                    | Tedarikçi: {row.get('Tedarikçi','—')}
                  </span>
                </div>
                """, unsafe_allow_html=True)

        # Stok doluluk grafiği
        if not df_st_filtre.empty and df_st_filtre["Maksimum Stok"].sum() > 0:
            df_st_filtre = df_st_filtre.copy()
            df_st_filtre["Doluluk %"] = (
                df_st_filtre["Stok Miktarı"] / df_st_filtre["Maksimum Stok"].replace(0, 1) * 100
            ).round(1).clip(upper=100)
            st.markdown("#### Stok Doluluk Oranları")
            st.bar_chart(df_st_filtre.set_index("Malzeme Adı")["Doluluk %"], height=240)

        # Tablo + Güncelleme + Yeni Malzeme + Excel Yükleme
        col_tbl, col_form = st.columns([3, 2])

        with col_tbl:
            st.markdown("#### Güncel Envanter Tablosu")
            goster_sutunlar = [s for s in STOK_SUTUNLARI if s in df_st_filtre.columns]
            st.dataframe(df_st_filtre[goster_sutunlar], use_container_width=True, hide_index=True)
            csv_stk = df_st_filtre.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                "📥 Envanter Listesi İndir", csv_stk,
                file_name=f"stok_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

        with col_form:
            # ── Manuel stok güncelle ──────────────────────────────────
            st.markdown("#### 🔧 Stok Girişi & Güncelleme")
            with st.form("stok_guncelle"):
                secilen_mal = st.selectbox("Malzeme", df_st_filtre["Malzeme Adı"].tolist())
                islem_tipi  = st.radio("İşlem", [
                    "Stok Girişi (Ekleme)",
                    "Stok Çıkışı (Kullanım)",
                    "Mutlak Değer Gir"
                ], horizontal=False)
                miktar      = st.number_input("Miktar", min_value=0, step=1, value=0)
                st.text_input("Not / Tedarikçi", placeholder="Opsiyonel")

                guncelle_btn = st.form_submit_button("💾 Kaydet", use_container_width=True)
                if guncelle_btn:
                    df_st2 = stok_df_getir()
                    mask_s = df_st2["Malzeme Adı"] == secilen_mal
                    mevcut = int(df_st2.loc[mask_s, "Stok Miktarı"].values[0])
                    if "Ekleme" in islem_tipi:
                        yeni_m = mevcut + miktar
                    elif "Çıkış" in islem_tipi:
                        if mevcut < miktar:
                            st.error(f"❌ Yetersiz stok! Mevcut: {mevcut}")
                            st.stop()
                        yeni_m = mevcut - miktar
                    else:
                        yeni_m = miktar
                    sb_update("stok", f"malzeme_adi=eq.{secilen_mal}", {
                        "stok_miktari": int(yeni_m),
                        "son_guncelleme": datetime.now().strftime("%d/%m/%Y")
                    })
                    cache_temizle()
                    log_yaz("STOK GÜNCELLEME", f"{secilen_mal} → {mevcut} → {yeni_m} ({islem_tipi})")
                    st.success(f"✅ {secilen_mal}: {mevcut} → **{yeni_m}**")
                    time.sleep(1)
                    st.rerun()

            if yetkili_mi("Yönetici"):
                st.markdown("---")

                # ── Excel / CSV ile toplu yükleme ─────────────────────
                st.markdown("#### 📂 Excel / CSV ile Toplu Stok Yükleme")
                st.caption("Şablon: Malzeme Kodu, Malzeme Adı, Kategori, Birim, Stok Miktarı, Kritik Seviye, Maksimum Stok, Son Fiyat (TL), Tedarikçi")

                # Şablon indir
                sablon_df = pd.DataFrame(columns=[
                    "Malzeme Kodu","Malzeme Adı","Kategori","Birim",
                    "Stok Miktarı","Kritik Seviye","Maksimum Stok",
                    "Son Fiyat (TL)","Tedarikçi"
                ])
                st.download_button(
                    "📥 Boş Şablon İndir (CSV)",
                    sablon_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                    file_name="stok_sablon.csv", mime="text/csv"
                )

                yukle_dosya = st.file_uploader(
                    "Excel (.xlsx) veya CSV (.csv) yükle",
                    type=["xlsx","csv"],
                    key="stok_yukle"
                )

                if yukle_dosya:
                    try:
                        if yukle_dosya.name.endswith(".xlsx"):
                            df_yukle = pd.read_excel(yukle_dosya, dtype=str)
                        else:
                            df_yukle = pd.read_csv(yukle_dosya, dtype=str)

                        st.markdown(f"**{len(df_yukle)} satır okundu.** Önizleme:")
                        st.dataframe(df_yukle.head(10), use_container_width=True, hide_index=True)

                        col_y1, col_y2 = st.columns(2)
                        with col_y1:
                            yukleme_modu = st.radio(
                                "Yükleme Modu",
                                ["Yeni ekle (var olanı atla)", "Güncelle (var olanın stokunu yaz)"],
                                key="yukle_mod"
                            )
                        with col_y2:
                            st.markdown("<br>", unsafe_allow_html=True)
                            yukle_btn = st.button("🚀 Yüklemeyi Başlat", use_container_width=True)

                        if yukle_btn:
                            df_mevcut = stok_df_getir()
                            eklenen = guncellenen = atlanan = 0
                            for _, satir in df_yukle.iterrows():
                                kod  = str(satir.get("Malzeme Kodu","")).strip()
                                ad   = str(satir.get("Malzeme Adı","")).strip()
                                if not ad:
                                    continue
                                mevcut_mi = (
                                    not df_mevcut.empty and
                                    (df_mevcut["Malzeme Kodu"] == kod).any()
                                )
                                veri = {
                                    "malzeme_kodu":  kod,
                                    "malzeme_adi":   ad,
                                    "kategori":      str(satir.get("Kategori","Diğer")).strip(),
                                    "birim":         str(satir.get("Birim","Adet")).strip(),
                                    "stok_miktari":  float(str(satir.get("Stok Miktarı",0)).replace(",",".") or 0),
                                    "kritik_seviye": float(str(satir.get("Kritik Seviye",0)).replace(",",".") or 0),
                                    "maksimum_stok": float(str(satir.get("Maksimum Stok",0)).replace(",",".") or 0),
                                    "son_fiyat":     float(str(satir.get("Son Fiyat (TL)",0)).replace(",",".") or 0),
                                    "tedarikci":     str(satir.get("Tedarikçi","")).strip(),
                                    "son_guncelleme": datetime.now().strftime("%d/%m/%Y")
                                }
                                if mevcut_mi:
                                    if "Güncelle" in yukleme_modu:
                                        sb_update("stok", f"malzeme_kodu=eq.{kod}", {
                                            "stok_miktari":  veri["stok_miktari"],
                                            "son_guncelleme": veri["son_guncelleme"]
                                        })
                                        guncellenen += 1
                                    else:
                                        atlanan += 1
                                else:
                                    sb_insert("stok", veri)
                                    eklenen += 1

                            cache_temizle()
                            log_yaz("TOPLU STOK YÜKLEME",
                                    f"Eklenen:{eklenen} Güncellenen:{guncellenen} Atlanan:{atlanan}")
                            st.success(
                                f"✅ Tamamlandı! "
                                f"**{eklenen}** yeni eklendi, "
                                f"**{guncellenen}** güncellendi, "
                                f"**{atlanan}** atlandı."
                            )
                            time.sleep(1)
                            st.rerun()

                    except Exception as e:
                        st.error(f"❌ Dosya okunamadı: {e}")

                st.markdown("---")

                # ── Tek tek yeni malzeme ekle ─────────────────────────
                st.markdown("#### ➕ Yeni Malzeme Tanımla")
                with st.form("yeni_malzeme"):
                    col_nm1, col_nm2 = st.columns(2)
                    with col_nm1:
                        y_kod  = st.text_input("Malzeme Kodu", placeholder="M009")
                        y_ad   = st.text_input("Malzeme Adı")
                        y_kat  = st.selectbox("Kategori", [
                            "Hareketli Parça","Sensör","Elektrik","Mekanik",
                            "Sarf","Hidrolik","Pnömatik","Elektronik","Diğer"
                        ])
                        y_bir  = st.selectbox("Birim", [
                            "Adet","Litre","Metre","Kg","Rulo","Kutu","Set","Takım"
                        ])
                    with col_nm2:
                        y_stok  = st.number_input("Başlangıç Stok",  min_value=0, step=1)
                        y_krit  = st.number_input("Kritik Seviye",    min_value=0, step=1)
                        y_maks  = st.number_input("Maksimum Stok",    min_value=0, step=1)
                        y_fiyat = st.number_input("Son Fiyat (TL)",   min_value=0, step=10)
                    y_tedarik = st.text_input("Tedarikçi")
                    ekle_btn  = st.form_submit_button("✅ Malzeme Ekle", use_container_width=True)
                    if ekle_btn and y_ad.strip():
                        df_st3 = stok_df_getir()
                        if y_kod and y_kod in df_st3["Malzeme Kodu"].values:
                            st.error("❌ Bu malzeme kodu zaten mevcut!")
                        else:
                            sb_insert("stok", {
                                "malzeme_kodu":  y_kod,
                                "malzeme_adi":   y_ad.strip(),
                                "kategori":      y_kat,
                                "birim":         y_bir,
                                "stok_miktari":  int(y_stok),
                                "kritik_seviye": int(y_krit),
                                "maksimum_stok": int(y_maks),
                                "son_fiyat":     float(y_fiyat),
                                "tedarikci":     y_tedarik,
                                "son_guncelleme": datetime.now().strftime("%d/%m/%Y")
                            })
                            cache_temizle()
                            log_yaz("YENİ MALZEME", f"{y_kod} — {y_ad}")
                            st.success(f"✅ {y_ad} eklendi!")
                            time.sleep(1)
                            st.rerun()


# =============================================================================
# SEKME 6: SİSTEM AYARLARI
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
                st.markdown(f"""
                <div class="durum-karti" style="padding:12px 16px;margin-bottom:8px;">
                  <span style="font-weight:600;color:#e2e8f0;">{k_bilgi['tam_ad']}</span>
                  <span style="font-size:12px;color:#64748b;margin-left:8px;">@{k_ad}</span>
                  <span class="sla-badge sla-ok" style="margin-left:8px;">{k_bilgi['rol']}</span>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")

            # ── Rol / Bilgi Güncelle ──────────────────────────────────
            st.markdown("#### ✏️ Kullanıcı Düzenle")
            with st.form("kullanici_duzenle"):
                duz_secim = st.selectbox(
                    "Düzenlenecek Kullanıcı",
                    list(kullanicilar.keys()),
                    format_func=lambda k: f"{kullanicilar[k]['tam_ad']} (@{k})"
                )
                col_duz1, col_duz2 = st.columns(2)
                with col_duz1:
                    duz_tamad = st.text_input(
                        "Ad Soyad",
                        value=kullanicilar[duz_secim]["tam_ad"]
                    )
                    duz_rol = st.selectbox(
                        "Rol",
                        ["Operatör", "Teknisyen", "Yönetici"],
                        index=["Operatör","Teknisyen","Yönetici"].index(
                            kullanicilar[duz_secim]["rol"]
                        )
                    )
                with col_duz2:
                    duz_sifre     = st.text_input("Yeni Şifre (boş bırakırsan değişmez)", type="password", placeholder="••••••")
                    duz_sifre_onay= st.text_input("Şifre Tekrar", type="password", placeholder="••••••")

                guncelle_btn = st.form_submit_button("💾 Değişiklikleri Kaydet", use_container_width=True)
                if guncelle_btn:
                    if duz_sifre and duz_sifre != duz_sifre_onay:
                        st.error("❌ Şifreler eşleşmiyor!")
                    else:
                        guncelle_veri = {
                            "tam_ad": duz_tamad.strip() or kullanicilar[duz_secim]["tam_ad"],
                            "rol": duz_rol
                        }
                        if duz_sifre:
                            guncelle_veri["sifre_hash"] = sifre_hashle(duz_sifre)
                        sb_update("kullanicilar", f"kullanici_adi=eq.{duz_secim}", guncelle_veri)
                        cache_temizle()
                        log_yaz("KULLANICI GÜNCELLENDİ", f"{duz_secim} → rol:{duz_rol}")
                        st.success(f"✅ {duz_secim} güncellendi! Yeni rol: **{duz_rol}**")
                        st.rerun()

            st.markdown("---")

            # ── Kullanıcı Sil ────────────────────────────────────────
            st.markdown("#### 🗑️ Kullanıcı Sil")
            with st.form("kullanici_sil"):
                aktif_k = st.session_state.get("aktif_kullanici", "")
                silinebilir = {k: v for k, v in kullanicilar.items() if k != aktif_k}
                sil_secim = st.selectbox(
                    "Silinecek Kullanıcı",
                    list(silinebilir.keys()),
                    format_func=lambda k: f"{silinebilir[k]['tam_ad']} (@{k})"
                ) if silinebilir else None
                sil_btn = st.form_submit_button("🗑️ Kullanıcıyı Sil", use_container_width=True)
                if sil_btn and sil_secim:
                    sb_delete("kullanicilar", f"kullanici_adi=eq.{sil_secim}")
                    cache_temizle()
                    log_yaz("KULLANICI SİLİNDİ", sil_secim)
                    st.success(f"✅ {sil_secim} silindi.")
                    st.rerun()

            st.markdown("---")

            # ── Yeni Kullanıcı Ekle ───────────────────────────────────
            st.markdown("#### ➕ Yeni Kullanıcı Ekle")
            with st.form("yeni_kullanici"):
                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    y_kullanici = st.text_input("Kullanıcı Adı")
                    y_sifre     = st.text_input("Şifre", type="password")
                with col_u2:
                    y_tamad = st.text_input("Ad Soyad")
                    y_rol   = st.selectbox("Rol", ["Operatör","Teknisyen","Yönetici"])
                kullanici_ekle = st.form_submit_button("Kullanıcı Oluştur", use_container_width=True)
                if kullanici_ekle:
                    if not all([y_kullanici, y_sifre, y_tamad]):
                        st.error("Tüm alanlar zorunludur.")
                    elif y_kullanici.lower() in kullanicilar:
                        st.error("Bu kullanıcı adı zaten mevcut.")
                    else:
                        sb_insert("kullanicilar", {
                            "kullanici_adi": y_kullanici.lower(),
                            "sifre_hash": sifre_hashle(y_sifre),
                            "rol": y_rol, "tam_ad": y_tamad
                        })
                        cache_temizle()
                        log_yaz("KULLANICI OLUŞTURULDU", f"{y_kullanici} — {y_rol}")
                        st.success(f"✅ {y_tamad} ({y_rol}) oluşturuldu!")
                        st.rerun()

        with col_a2:
            st.markdown("#### 📜 Sistem Aktivite Logu")
            try:
                log_rows = sb_select("sistem_log")
                if log_rows:
                    df_log = pd.DataFrame(log_rows).rename(columns={
                        "zaman":"Zaman","kullanici":"Kullanıcı","islem":"İşlem","detay":"Detay"
                    })
                    st.dataframe(
                        df_log.sort_values("Zaman", ascending=False).head(50),
                        use_container_width=True, hide_index=True
                    )
                    log_csv = df_log.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
                    st.download_button(
                        "📥 Log İndir", log_csv,
                        file_name=f"sistem_log_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("Henüz aktivite kaydı yok.")
            except Exception as e:
                st.info(f"Log yüklenemedi: {e}")

            st.markdown("---")
            st.markdown("#### 🗄️ Veri Yedekleme")
            col_bk1, col_bk2 = st.columns(2)
            with col_bk1:
                df_yedek = ariza_df_getir()
                if not df_yedek.empty:
                    st.download_button(
                        "💾 Arıza DB Yedeği",
                        df_yedek.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                        file_name=f"ariza_db_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv", use_container_width=True
                    )
            with col_bk2:
                df_stok_yedek = stok_df_getir()
                if not df_stok_yedek.empty:
                    st.download_button(
                        "💾 Stok DB Yedeği",
                        df_stok_yedek.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"),
                        file_name=f"stok_db_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv", use_container_width=True
                    )

        # Tehlikeli Bölge
        st.markdown("---")

        # ── Makine Yönetimi ───────────────────────────────────────────
        with st.expander("🏭 Makine Listesi Yönetimi", expanded=False):
            st.caption("Bölge bazlı makine ekle / sil. Değişiklikler anında tüm formlara yansır.")
            col_mk1, col_mk2 = st.columns([3, 2])

            with col_mk1:
                mk_rows = sb_select("makine_listesi", "aktif=eq.true")
                if mk_rows:
                    df_mk = pd.DataFrame(mk_rows)[["id","bolge","makine_adi"]]
                    df_mk.columns = ["ID","Bölge","Makine Adı"]
                    st.dataframe(df_mk.drop(columns=["ID"]), use_container_width=True, hide_index=True)
                else:
                    st.info("Henüz dinamik makine eklenmemiş. Sabit liste kullanılıyor.")

            with col_mk2:
                with st.form("makine_ekle_form"):
                    mk_bolge = st.selectbox("Bölge", BOLGELER, key="mk_bolge")
                    mk_ad    = st.text_input("Makine Adı", placeholder="Örn: VNA-05 (Hat C)")
                    mk_ekle  = st.form_submit_button("➕ Makine Ekle", use_container_width=True)
                    if mk_ekle and mk_ad.strip():
                        sb_insert("makine_listesi", {
                            "bolge": mk_bolge,
                            "makine_adi": mk_ad.strip(),
                            "aktif": True
                        })
                        cache_temizle()
                        log_yaz("MAKİNE EKLENDİ", f"{mk_bolge} — {mk_ad}")
                        st.success(f"✅ {mk_ad} eklendi!")
                        st.rerun()

            # Silme
            if mk_rows:
                st.markdown("**Makine Sil:**")
                sil_secenekler = {f"{r['bolge']} — {r['makine_adi']}": r["id"] for r in mk_rows}
                col_ms1, col_ms2 = st.columns([3,1])
                with col_ms1:
                    sil_mk = st.selectbox("Silinecek makine", list(sil_secenekler.keys()), key="mk_sil_sec")
                with col_ms2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑️ Sil", key="mk_sil_btn", use_container_width=True):
                        sb_delete("makine_listesi", f"id=eq.{sil_secenekler[sil_mk]}")
                        cache_temizle()
                        log_yaz("MAKİNE SİLİNDİ", sil_mk)
                        st.success(f"✅ Silindi: {sil_mk}")
                        st.rerun()

        # ── Arıza Türü Yönetimi ───────────────────────────────────────
        with st.expander("⚙️ Arıza Türü Yönetimi", expanded=False):
            st.caption("Arıza kategorisi ve alt tür ekle / sil. Değişiklikler anında formlara yansır.")
            col_at1, col_at2 = st.columns([3, 2])

            with col_at1:
                at_rows = sb_select("ariza_turu_listesi", "aktif=eq.true")
                if at_rows:
                    df_at = pd.DataFrame(at_rows)[["id","kategori","alt_tur"]]
                    df_at.columns = ["ID","Kategori","Alt Tür"]
                    st.dataframe(df_at.drop(columns=["ID"]), use_container_width=True, hide_index=True)
                else:
                    st.info("Henüz dinamik arıza türü eklenmemiş. Sabit liste kullanılıyor.")

            with col_at2:
                # Mevcut kategoriler + yeni kategori seçeneği
                mevcut_kategoriler = list(ARIZA_TURLERI.keys())
                if at_rows:
                    db_kategoriler = list({r["kategori"] for r in at_rows})
                    mevcut_kategoriler = sorted(set(mevcut_kategoriler + db_kategoriler))

                with st.form("ariza_turu_ekle_form"):
                    at_kat_sec = st.selectbox(
                        "Kategori (mevcut seç)",
                        ["— Yeni kategori gir —"] + mevcut_kategoriler,
                        key="at_kat_sec"
                    )
                    at_kat_yeni = st.text_input(
                        "Yeni Kategori Adı",
                        placeholder="Örn: 🔩 Bağlantı Elemanları",
                        help="Yeni kategori eklemek istiyorsanız doldurun"
                    )
                    at_alt = st.text_input("Alt Tür", placeholder="Örn: Cıvata gevşemesi")
                    at_ekle = st.form_submit_button("➕ Ekle", use_container_width=True)

                    if at_ekle and at_alt.strip():
                        kategori = at_kat_yeni.strip() if at_kat_sec == "— Yeni kategori gir —" else at_kat_sec
                        if kategori:
                            sb_insert("ariza_turu_listesi", {
                                "kategori": kategori,
                                "alt_tur":  at_alt.strip(),
                                "aktif":    True
                            })
                            cache_temizle()
                            log_yaz("ARIZA TÜRÜ EKLENDİ", f"{kategori} — {at_alt}")
                            st.success(f"✅ {kategori} → {at_alt} eklendi!")
                            st.rerun()
                        else:
                            st.error("Kategori adı boş olamaz!")

            # Silme
            if at_rows:
                st.markdown("**Arıza Türü Sil:**")
                sil_at_sec = {f"{r['kategori']} — {r['alt_tur']}": r["id"] for r in at_rows}
                col_as1, col_as2 = st.columns([3,1])
                with col_as1:
                    sil_at = st.selectbox("Silinecek tür", list(sil_at_sec.keys()), key="at_sil_sec")
                with col_as2:
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🗑️ Sil", key="at_sil_btn", use_container_width=True):
                        sb_delete("ariza_turu_listesi", f"id=eq.{sil_at_sec[sil_at]}")
                        cache_temizle()
                        log_yaz("ARIZA TÜRÜ SİLİNDİ", sil_at)
                        st.success(f"✅ Silindi: {sil_at}")
                        st.rerun()

        st.markdown("---")
        with st.expander("🗑️ Tehlikeli İşlemler (Veri Temizleme)"):
            st.warning("⚠️ Bu işlemler geri alınamaz!")
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                if st.button("🗑️ Kapalı Talepleri Temizle", use_container_width=True):
                    sb_delete("ariza_kayitlari", "durum=eq.Kapalı")
                    cache_temizle()
                    log_yaz("VERİ TEMİZLEME", "Kapalı talepler silindi")
                    st.success("Kapalı talepler temizlendi.")
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
  <span style="color:#1d4ed8;">Enterprise Edition</span>
</div>
""", unsafe_allow_html=True)
