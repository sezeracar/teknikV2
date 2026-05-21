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
# SUPABASE BAĞLANTI KATMANI
# =============================================================================

def sb_url() -> str:
    return st.secrets["supabase"]["url"]

def sb_key() -> str:
    return st.secrets["supabase"]["key"]

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
    """Tablodan veri çek. filtre örn: 'durum=eq.Açık' """
    url = f"{sb_url()}/rest/v1/{tablo}?{filtre}&order=id.desc" if filtre else \
          f"{sb_url()}/rest/v1/{tablo}?order=id.desc"
    r = requests.get(url, headers=sb_headers(), timeout=10)
    return r.json() if r.ok else []

def sb_insert(tablo: str, veri: dict) -> bool:
    url = f"{sb_url()}/rest/v1/{tablo}"
    r = requests.post(url, headers=sb_headers(), json=veri, timeout=10)
    return r.ok

def sb_update(tablo: str, filtre: str, veri: dict) -> bool:
    url = f"{sb_url()}/rest/v1/{tablo}?{filtre}"
    h = sb_headers()
    h["Prefer"] = "return=minimal"
    r = requests.patch(url, headers=h, json=veri, timeout=10)
    return r.ok

def sb_delete(tablo: str, filtre: str) -> bool:
    url = f"{sb_url()}/rest/v1/{tablo}?{filtre}"
    r = requests.delete(url, headers=sb_headers(), timeout=10)
    return r.ok

# ── Yardımcı: Supabase listesini DataFrame'e çevir ────────────────────────

def sb_to_df(rows: list, kolon_map: dict = None) -> pd.DataFrame:
    """Supabase JSON listesini Türkçe kolon adlı DataFrame'e çevirir."""
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    if kolon_map:
        df = df.rename(columns=kolon_map)
    return df

# ── Kolon eşleştirme haritaları ───────────────────────────────────────────

ARIZA_KOLON_MAP = {
    "talep_no":            "Talep No",
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
    rows = sb_select("ariza_kayitlari")
    return sb_to_df(rows, ARIZA_KOLON_MAP)

@st.cache_data(ttl=30)
def stok_df_getir() -> pd.DataFrame:
    rows = sb_select("stok")
    return sb_to_df(rows, STOK_KOLON_MAP)

@st.cache_data(ttl=60)
def kullanicilar_getir() -> dict:
    rows = sb_select("kullanicilar")
    return {r["kullanici_adi"]: {"sifre": r["sifre_hash"],
                                  "rol":   r["rol"],
                                  "tam_ad":r["tam_ad"]} for r in rows}

def cache_temizle():
    ariza_df_getir.clear()
    stok_df_getir.clear()
    kullanicilar_getir.clear()

# ── Veritabanı başlatma: tablolar boşsa varsayılan verileri yaz ───────────

def veritabani_hazirla():
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
    return kullanicilar_getir()



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
        acik  = len(df_sb[df_sb["Durum"] == "Açık"])
        kritik= len(df_sb[(df_sb["Durum"]=="Açık") & (df_sb["Öncelik"].str.startswith("🔴", na=False))])
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

    # ── KPI Kartlar ───────────────────────────────────────────────────
    toplam   = len(df)
    acik     = len(df[df["Durum"] == "Açık"])
    kapali   = len(df[df["Durum"] == "Kapalı"])
    kritik   = len(df[(df["Durum"]=="Açık") & (df["Öncelik"].str.startswith("🔴", na=False))])
    sla_asan = len(df[df["SLA Durumu"].str.contains("Aşıldı", na=False)])

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("📋 Toplam Talep",    toplam,  delta=f"+{len(df[df['Açılış Tarihi'].str.startswith(datetime.now().strftime('%d/%m/%Y'), na=False)])} bugün")
    with col2: st.metric("🟡 Açık Talepler",   acik,    delta=None)
    with col3: st.metric("✅ Kapatılan",        kapali,  delta=f"Kapatma oranı: %{round(kapali/max(toplam,1)*100)}")
    with col4: st.metric("🔴 Kritik Açık",      kritik,  delta="acil müdahale" if kritik > 0 else "Temiz")
    with col5: st.metric("⚠️ SLA Aşımı",       sla_asan, delta=None)

    st.markdown("---")

    if len(df) == 0:
        st.info("📭 Sistemde henüz kayıt bulunmuyor. 'Yeni Talep Aç' sekmesinden ilk arızayı ekleyin.")
    else:
        # ── Grafikler ─────────────────────────────────────────────────
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown("#### Öncelik Bazlı Açık Talepler")
            if acik > 0:
                acik_df = df[df["Durum"] == "Açık"]
                onc_say = acik_df["Öncelik"].value_counts()
                onc_say.index = [i[:30] for i in onc_say.index]
                st.bar_chart(onc_say, height=260)
            else:
                st.info("Açık talep yok")

        with col_g2:
            st.markdown("#### Makine Bazlı Arıza Sayısı")
            mak_say = df["Makine"].value_counts().head(8)
            st.bar_chart(mak_say, height=260)

        # ── Günlük Trend ──────────────────────────────────────────────
        st.markdown("#### 30 Günlük Arıza Trendi")
        try:
            df_trend = df.copy()
            df_trend["Tarih"] = pd.to_datetime(
                df_trend["Açılış Tarihi"], format="%d/%m/%Y %H:%M", errors="coerce"
            ).dt.date
            son_30  = date.today() - timedelta(days=30)
            df_trend = df_trend[df_trend["Tarih"] >= son_30]
            gunluk  = df_trend.groupby("Tarih").size().rename("Arıza Sayısı")
            if len(gunluk) > 0:
                st.line_chart(gunluk, height=200)
        except Exception as e:
            st.caption(f"Trend verisi işlenemedi: {e}")

        # ── Açık Talepler Listesi ──────────────────────────────────────
        st.markdown("---")
        st.markdown("#### 🟡 Müdahale Bekleyen Açık Talepler")
        acik_df = df[df["Durum"]=="Açık"].copy()
        if acik_df.empty:
            st.success("✅ Müdahale bekleyen açık talep bulunmuyor.")
        else:
            # Kritik uyarı
            k_df = acik_df[acik_df["Öncelik"].str.startswith("🔴", na=False)]
            if not k_df.empty:
                st.markdown(f"""
                <div class="kritik-banner">
                  <strong style="color:#f87171;">🚨 {len(k_df)} adet ÜRETİM DURDURUCU kritik arıza tespit edildi!</strong>
                  <span style="color:#94a3b8;font-size:12px;margin-left:8px;">
                    Makine(ler): {', '.join(k_df['Makine'].unique()[:3])}
                  </span>
                </div>
                """, unsafe_allow_html=True)

            goster_sutunlar = ["Talep No","Öncelik","Açılış Tarihi","Bildiren","Makine","Arıza Türü","Arıza Tanımı","SLA Durumu"]
            goster_sutunlar = [s for s in goster_sutunlar if s in acik_df.columns]
            st.dataframe(
                acik_df[goster_sutunlar].sort_values("Açılış Tarihi", ascending=False),
                use_container_width=True, hide_index=True
            )


# =============================================================================
# SEKME 2: YENİ TALEP AÇ (HERKESE AÇIK)
# =============================================================================

with tab_yeni:
    st.markdown("### ➕ Yeni Arıza Bildirimi Oluştur")
    st.caption("Bu form tüm personele açıktır. Oturum açmadan da kullanılabilir.")

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

        st.markdown("#### 🏭 Arıza Lokasyonu & Tipi")
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            makine    = st.selectbox("Makine / Sistem *", MAKINE_LISTESI)
            ariza_tur = st.selectbox("Arıza Kategorisi *", list(ARIZA_TURLERI.keys()))
        with col_m2:
            oncelik      = st.selectbox("Kritiklik Seviyesi (SLA) *", list(ARIZA_ONCELIKLERI.keys()))
            bildirim_saat= st.time_input("Arıza Fark Edilme Saati", datetime.now().time())

        alt_kategori = st.selectbox(
            "Alt Kategori",
            ARIZA_TURLERI[ariza_tur],
            help="Arıza tipini daha spesifik tanımlayın"
        )
        ariza_tanimi = st.text_area(
            "Arıza Tanımı *",
            placeholder="Arızanın belirti ve etkilerini kısaca açıklayın. Örn: VNA-01 sürüş motorunda aşırı titreşim ve hata kodu E-045...",
            height=100
        )
        foto_notu = st.text_input(
            "Fotoğraf / Referans Notu",
            placeholder="Fotoğraf çekildiyse referans kodu veya açıklama girin"
        )

        # SLA bilgi kutusu
        sla_bilgi = ARIZA_ONCELIKLERI[oncelik]
        st.markdown(f"""
        <div style="background:rgba(30,41,59,0.6);border:1px solid rgba(99,179,237,0.15);
                    border-radius:8px;padding:12px 16px;margin:8px 0;font-size:12px;">
          ⏱ <strong style="color:#93c5fd;">SLA Hedefi:</strong>
          <span style="color:#cbd5e1;"> Bu seviye için hedef müdahale süresi:
            <strong style="color:#fbbf24;">{sla_bilgi['sla_dk']} dakika</strong>
          </span>
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
                    "talep_no": no, "durum": "Açık", "oncelik": oncelik,
                    "vardiya": vardiya, "acilis_tarihi": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "kapatma_tarihi": "", "bildiren": bildiren.strip(),
                    "bildiren_departman": bildiren_dept, "mudahale_eden": "",
                    "makine": makine, "ariza_turu": ariza_tur, "alt_kategori": alt_kategori,
                    "ariza_tanimi": ariza_tanimi.strip(),
                    "bildirim_saati": bildirim_saat if isinstance(bildirim_saat, str) else str(bildirim_saat),
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
                log_yaz("YENİ TALEP", f"{no} — {makine} — {bildiren}")
                st.success(f"""
                ✅ **Talep Başarıyla Oluşturuldu!**
                Talep No: **{no}** | Öncelik: {oncelik} | SLA: {sla_bilgi['sla_dk']} dk
                """)
                time.sleep(1)
                st.rerun()


# =============================================================================
# SEKME 3: TALEP KAPAT
# =============================================================================

with tab_kapat:
    if not giris_gerektir("Teknisyen"):
        pass
    else:
        df_k = ariza_df_getir()
        acik_k = df_k[df_k["Durum"]=="Açık"].copy()

        if acik_k.empty:
            st.success("🎉 Müdahale bekleyen açık talep bulunmuyor. Harika iş!")
        else:
            # Kritik uyarı
            krit_k = acik_k[acik_k["Öncelik"].str.startswith("🔴", na=False)]
            if not krit_k.empty:
                st.markdown(f"""
                <div class="kritik-banner">
                  <strong style="color:#f87171;">🚨 {len(krit_k)} KRİTİK ARIZA</strong>
                  <span style="color:#94a3b8;font-size:12px;"> — Acil müdahale bekliyor</span>
                </div>
                """, unsafe_allow_html=True)

            # Talep seçimi
            col_s1, col_s2 = st.columns([2,1])
            with col_s1:
                secenekler = acik_k.apply(
                    lambda r: f"[{r['Talep No']}] {r['Öncelik'][:2]} {r['Makine']} — {str(r['Arıza Tanımı'])[:60]}",
                    axis=1
                ).tolist()
                secilen = st.selectbox("📋 Kapatılacak Talebi Seçin", secenekler)

            secilen_no = secilen.split("]")[0].replace("[","").strip()
            talep = df_k[df_k["Talep No"] == secilen_no].iloc[0]

            # Talep detay kartı
            sla_bilgi_g = sla_hesapla(talep["Öncelik"], talep["Açılış Tarihi"])
            sla_cls = "sla-ok" if "İçinde" in sla_bilgi_g["durum"] else "sla-warn"
            st.markdown(f"""
            <div class="durum-karti">
              <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:12px;">
                <div>
                  <span style="font-size:11px;color:#64748b;font-weight:700;text-transform:uppercase;
                               letter-spacing:0.08em;">TALEP DETAYI</span>
                  <div style="font-size:20px;font-weight:700;color:#e2e8f0;margin-top:4px;">
                    {talep['Talep No']}
                  </div>
                </div>
                <span class="sla-badge {sla_cls}">{sla_bilgi_g['durum']}</span>
              </div>
              <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;font-size:13px;">
                <div><span style="color:#64748b;">Makine</span><br>
                     <strong style="color:#e2e8f0;">{talep['Makine']}</strong></div>
                <div><span style="color:#64748b;">Bildiren</span><br>
                     <strong style="color:#e2e8f0;">{talep['Bildiren']}</strong></div>
                <div><span style="color:#64748b;">Açılış</span><br>
                     <strong style="color:#e2e8f0;">{talep['Açılış Tarihi']}</strong></div>
                <div><span style="color:#64748b;">Arıza Türü</span><br>
                     <strong style="color:#e2e8f0;">{talep['Arıza Türü']}</strong></div>
                <div><span style="color:#64748b;">Geçen Süre</span><br>
                     <strong style="color:#fbbf24;">{sla_bilgi_g['gecen_dk']} dk / {sla_bilgi_g['sla_dk']} dk SLA</strong></div>
                <div><span style="color:#64748b;">SLA Oranı</span><br>
                     <strong style="color:#{'f87171' if sla_bilgi_g['oran']>100 else '4ade80'};">%{sla_bilgi_g['oran']}</strong></div>
              </div>
              <div style="margin-top:12px;padding-top:10px;border-top:1px solid rgba(99,179,237,0.1);
                          font-size:13px;color:#94a3b8;">
                📝 <em>{talep['Arıza Tanımı']}</em>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Kapatma Formu
            st.markdown("#### 🔧 Müdahale & Çözüm Bilgileri")
            with st.form("kapat_formu"):
                col_k1, col_k2 = st.columns(2)
                with col_k1:
                    mudahale_eden  = st.text_input(
                        "Müdahale Eden Teknisyen *",
                        value=st.session_state.get("aktif_tam_ad","")
                    )
                    mudahale_saat  = st.text_input(
                        "Müdahale Saat Aralığı",
                        placeholder="Örn: 14:00 – 14:45",
                        value=f"{datetime.now().strftime('%H:%M')} – "
                    )
                    isguc_maliyet  = st.number_input("İş Gücü Maliyeti (TL)", min_value=0, step=50, value=0)
                with col_k2:
                    kapatma_zaman  = st.text_input(
                        "Kapatma Tarihi & Saati",
                        value=datetime.now().strftime("%d/%m/%Y %H:%M")
                    )
                    cozum_suresi   = st.number_input("Toplam Çözüm Süresi (Dakika) *", min_value=1, step=5, value=30)
                    malzeme_maliyet= st.number_input("Malzeme Maliyeti (TL)", min_value=0, step=50, value=0)

                cozum_aciklama = st.text_area(
                    "Uygulanan Çözüm & Teknik Notlar *",
                    placeholder="Yapılan müdahaleyi detaylı açıklayın. Değiştirilen parça, ayarlama, sıfırlama vb.",
                    height=100
                )

                col_k3, col_k4 = st.columns(2)
                with col_k3:
                    kok_neden   = st.selectbox("Kök Neden Kategorisi", [
                        "Yağlama eksikliği", "Aşınma (ömür tükenmesi)", "Hatalı kullanım",
                        "Yetersiz bakım periyodu", "Tasarım/malzeme yetersizliği",
                        "Dış etken (toz, nem, darbe)", "Yazılım/donanım arızası", "Bilinmiyor", "Diğer"
                    ])
                with col_k4:
                    kapatma_onayi = st.selectbox("Kapatma Onayı", [
                        "Teknisyen Onayı", "Vardiya Amiri Onayı", "Bakım Müdürü Onayı"
                    ])

                neden_analizi  = st.text_area(
                    "5 Neden Analizi",
                    placeholder="Neden 1: ...\nNeden 2: ...\nNeden 3: ...\nNeden 4: ...\nNeden 5 (Kök Neden): ...",
                    height=110
                )
                kaizen = st.text_area(
                    "Kaizen / İyileştirme Önerisi",
                    placeholder="Arızanın tekrarlanmaması için neler yapılabilir?",
                    height=80
                )

                st.markdown("#### 📦 Kullanılan Malzemeler")
                df_stok_k = stok_df_getir()
                col_stk1, col_stk2 = st.columns(2)
                with col_stk1:
                    malzeme_secim = st.selectbox(
                        "Stoktan Malzeme",
                        ["—  Malzeme Kullanılmadı"] + df_stok_k["Malzeme Adı"].tolist()
                    )
                with col_stk2:
                    malzeme_adet  = st.number_input("Kullanılan Miktar", min_value=0, step=1, value=0)

                submit_kapat = st.form_submit_button("✅ Talebi Kapat & Kaydet", use_container_width=True)

                if submit_kapat:
                    if not cozum_aciklama.strip():
                        st.error("❌ Çözüm açıklaması zorunludur.")
                    else:
                        malzeme_metni = "—"
                        if "—" not in malzeme_secim and malzeme_adet > 0:
                            stok_mik = int(df_stok_k.loc[
                                df_stok_k["Malzeme Adı"]==malzeme_secim, "Stok Miktarı"
                            ].values[0])
                            if stok_mik < malzeme_adet:
                                st.error(f"❌ Yetersiz stok! Mevcut: {stok_mik} adet")
                                st.stop()
                            yeni_stok = stok_mik - malzeme_adet
                            # Stok Supabase güncelle
                            sb_update("stok", f"malzeme_adi=eq.{malzeme_secim}", {
                                "stok_miktari": yeni_stok,
                                "son_guncelleme": datetime.now().strftime("%d/%m/%Y")
                            })
                            malzeme_metni = f"{malzeme_secim} x {malzeme_adet}"

                        toplam_maliyet = isguc_maliyet + malzeme_maliyet
                        sla_s = sla_hesapla(talep["Öncelik"], talep["Açılış Tarihi"], kapatma_zaman)

                        # Arıza kaydını Supabase'de güncelle
                        sb_update("ariza_kayitlari", f"talep_no=eq.{secilen_no}", {
                            "durum":               "Kapalı",
                            "kapatma_tarihi":      str(kapatma_zaman),
                            "mudahale_eden":       str(mudahale_eden),
                            "ilk_mudahale_saati":  str(mudahale_saat),
                            "cozum_suresi_dk":     int(cozum_suresi),
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

                        log_yaz("TALEP KAPATILDI", f"{secilen_no} — {mudahale_eden} — {cozum_suresi} dk")
                        st.success(f"""
                        ✅ **Talep {secilen_no} başarıyla kapatıldı!**
                        Çözüm Süresi: {cozum_suresi} dk | Toplam Maliyet: {toplam_maliyet:,.0f} TL | {sla_s['durum']}
                        """)
                        time.sleep(1.5)
                        st.rerun()


# =============================================================================
# SEKME 4: RAPORLAMA & ARŞİV
# =============================================================================

with tab_rapor:
    if not giris_gerektir("Teknisyen"):
        pass
    else:
        st.markdown("### 📋 Arıza Arşivi & Gelişmiş Raporlama")
        df_r = ariza_df_getir()

        # ── Filtreler ──────────────────────────────────────────────────
        with st.expander("🔍 Filtrele & Ara", expanded=True):
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                f_durum   = st.selectbox("Durum",    ["Tümü", "Açık", "Kapalı"])
            with col_f2:
                f_oncelik = st.selectbox("Öncelik",  ["Tümü"] + list(ARIZA_ONCELIKLERI.keys()))
            with col_f3:
                f_makine  = st.selectbox("Makine",   ["Tümü"] + MAKINE_LISTESI)
            with col_f4:
                f_tur     = st.selectbox("Arıza Türü", ["Tümü"] + list(ARIZA_TURLERI.keys()))

            col_t1, col_t2, col_t3 = st.columns([2,2,2])
            with col_t1:
                f_bas = st.date_input("Başlangıç", date(2025,1,1))
            with col_t2:
                f_bit = st.date_input("Bitiş",     date.today())
            with col_t3:
                f_arama = st.text_input("🔍 Metin Ara", placeholder="Talep no, personel, makine...")

        # Filtre uygula
        goster = df_r.copy()
        if f_durum   != "Tümü": goster = goster[goster["Durum"]   == f_durum]
        if f_oncelik != "Tümü": goster = goster[goster["Öncelik"] == f_oncelik]
        if f_makine  != "Tümü": goster = goster[goster["Makine"]  == f_makine]
        if f_tur     != "Tümü": goster = goster[goster["Arıza Türü"] == f_tur]
        if f_arama.strip():
            mask = goster.apply(lambda r: r.astype(str).str.contains(f_arama, case=False, na=False).any(), axis=1)
            goster = goster[mask]
        try:
            goster["_tarih"] = pd.to_datetime(goster["Açılış Tarihi"], format="%d/%m/%Y %H:%M", errors="coerce").dt.date
            goster = goster[(goster["_tarih"] >= f_bas) & (goster["_tarih"] <= f_bit)].drop(columns=["_tarih"])
        except: pass

        # Özet satır
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
            try:    sla_asan_r = len(goster[goster["SLA Durumu"].str.contains("Aşıldı",na=False)])
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

        st.dataframe(
            goster.sort_values("Açılış Tarihi", ascending=False),
            use_container_width=True, hide_index=True
        )

        # Seçili talebin tam detayı
        if len(goster) > 0:
            with st.expander("📄 Talep Detay Görüntüle"):
                secim_no = st.selectbox("Talep seçin", goster["Talep No"].tolist())
                secim_satir = goster[goster["Talep No"] == secim_no]
                if not secim_satir.empty:
                    s = secim_satir.iloc[0]
                    col_d1, col_d2 = st.columns(2)
                    alanlar = list(ARIZA_SUTUNLARI)
                    yari = len(alanlar) // 2
                    with col_d1:
                        for alan in alanlar[:yari]:
                            if alan in s.index and str(s[alan]) not in ["", "nan"]:
                                st.markdown(f"**{alan}:** {s[alan]}")
                    with col_d2:
                        for alan in alanlar[yari:]:
                            if alan in s.index and str(s[alan]) not in ["", "nan"]:
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

        # Kritik stok alarmları
        kritik_stok = df_st[df_st["Stok Miktarı"] <= df_st["Kritik Seviye"]]
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

        # Stok doluluk oranı grafiği
        df_st["Doluluk %"] = (
            df_st["Stok Miktarı"] / df_st["Maksimum Stok"].replace(0, 1) * 100
        ).round(1).clip(upper=100)

        st.markdown("#### Stok Doluluk Oranları")
        st.bar_chart(
            df_st.set_index("Malzeme Adı")["Doluluk %"],
            height=260
        )

        # Tablo + Güncelleme Formu
        col_tbl, col_form = st.columns([3, 2])

        with col_tbl:
            st.markdown("#### Güncel Envanter Tablosu")
            goster_sutunlar = [s for s in STOK_SUTUNLARI if s in df_st.columns]
            st.dataframe(df_st[goster_sutunlar], use_container_width=True, hide_index=True)
            csv_stk = df_st.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                "📥 Envanter Listesi İndir", csv_stk,
                file_name=f"stok_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

        with col_form:
            st.markdown("#### Stok Girişi & Güncelleme")
            with st.form("stok_guncelle"):
                secilen_mal = st.selectbox("Malzeme", df_st["Malzeme Adı"].tolist())
                islem_tipi  = st.radio("İşlem", ["Stok Girişi (Ekleme)", "Stok Çıkışı (Kullanım)", "Mutlak Değer Gir"], horizontal=False)
                miktar      = st.number_input("Miktar", min_value=0, step=1, value=0)
                aciklama    = st.text_input("Not / Tedarikçi", placeholder="Opsiyonel")

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

            # Yeni malzeme ekle (sadece Yönetici)
            if yetkili_mi("Yönetici"):
                st.markdown("---")
                st.markdown("#### ➕ Yeni Malzeme Tanımla")
                with st.form("yeni_malzeme"):
                    y_kod  = st.text_input("Malzeme Kodu", placeholder="M009")
                    y_ad   = st.text_input("Malzeme Adı")
                    y_kat  = st.selectbox("Kategori", ["Hareketli Parça","Sensör","Elektrik","Mekanik","Sarf","Diğer"])
                    y_bir  = st.selectbox("Birim", ["Adet","Litre","Metre","Kg","Rulo","Kutu"])
                    col_yn1, col_yn2 = st.columns(2)
                    with col_yn1:
                        y_stok = st.number_input("Başlangıç Stok", min_value=0, step=1)
                        y_krit = st.number_input("Kritik Seviye",  min_value=0, step=1)
                    with col_yn2:
                        y_maks = st.number_input("Maksimum Stok",  min_value=0, step=1)
                        y_fiyat= st.number_input("Son Fiyat (TL)", min_value=0, step=10)
                    y_tedarik = st.text_input("Tedarikçi")
                    ekle_btn  = st.form_submit_button("Malzeme Ekle", use_container_width=True)
                    if ekle_btn and y_ad.strip():
                        df_st3 = stok_df_getir()
                        if y_kod in df_st3["Malzeme Kodu"].values:
                            st.error("Bu kod zaten mevcut!")
                        else:
                            sb_insert("stok", {
                                "malzeme_kodu": y_kod, "malzeme_adi": y_ad.strip(),
                                "kategori": y_kat, "birim": y_bir,
                                "stok_miktari": int(y_stok), "kritik_seviye": int(y_krit),
                                "maksimum_stok": int(y_maks), "son_fiyat": float(y_fiyat),
                                "tedarikci": y_tedarik,
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
