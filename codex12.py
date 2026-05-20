# -*- coding: utf-8 -*-
"""
=============================================================================
TEKNIK BAKIM & ARIZA YÖNETİM SİSTEMİ v2.0
Enterprise-Grade TPM & CMMS Platform
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

# =============================================================================
# SABITLER VE YAPILANDIRMA
# =============================================================================

DB_FILE        = "ariza_kayitlari.csv"
STOK_FILE      = "yedek_parca_stok.csv"
KULLANICI_FILE = "kullanicilar.json"
LOG_FILE       = "sistem_log.csv"

MAKINE_LISTESI = [
    "VNA-01 (Hat A)", "VNA-02 (Hat A)", "VNA-03 (Hat B)",
    "RT-01 (Depo Sahası)", "RT-02 (Depo Sahası)",
    "Konveyör Hattı 1", "Konveyör Hattı 2",
    "Kompresör İstasyonu", "Elektrik Panosu MCC-1",
    "Soğutma Ünitesi", "Forklift FLT-01", "Diğer"
]

ARIZA_TURLERI = {
    "⚡ Elektrik":   ["Sigorta attı", "Motor arızası", "Sensör hatası", "PLC/Otomasyon", "Kablo kopması", "Diğer"],
    "⚙️ Mekanik":    ["Rulman arızası", "Kayış/Zincir kopması", "Dişli hasarı", "Aşınma", "Titreşim", "Diğer"],
    "🔧 Tesisat":    ["Boru sızıntısı", "Valf arızası", "Pompa sorunu", "Basınç düşüklüğü", "Diğer"],
    "🖥️ Elektronik": ["HMI ekran hatası", "Ağ bağlantı sorunu", "Yazılım hatası", "Diğer"],
    "🏗️ Yapısal":    ["Kafes/Yapı hasarı", "Zemin sorunu", "Diğer"]
}

ARIZA_ONCELIKLERI = {
    "🔴 KRİTİK — Üretim Durdu":   {"renk": "#DC2626", "sla_dk": 30,  "puan": 1},
    "🟠 YÜKSEK — Kısmi Aksama":   {"renk": "#EA580C", "sla_dk": 120, "puan": 2},
    "🟡 ORTA — Performans Düşük": {"renk": "#D97706", "sla_dk": 480, "puan": 3},
    "🟢 DÜŞÜK — Planlı Bakım":    {"renk": "#16A34A", "sla_dk": 1440,"puan": 4},
}

KULLANICILAR_DEFAULT = {
    "admin":       {"sifre": hashlib.sha256("1905".encode()).hexdigest(), "rol": "Yönetici",   "tam_ad": "Sistem Yöneticisi"},
    "sezer":       {"sifre": hashlib.sha256("1905".encode()).hexdigest(), "rol": "Yönetici",   "tam_ad": "Sezer Bey"},
    "teknik01":    {"sifre": hashlib.sha256("1905".encode()).hexdigest(), "rol": "Teknisyen",  "tam_ad": "Teknisyen 1"},
    "uretim":      {"sifre": hashlib.sha256("1905".encode()).hexdigest(), "rol": "Operatör",   "tam_ad": "Üretim Operatörü"},
}

ARIZA_SUTUNLARI = [
    "Talep No", "Durum", "Öncelik", "Vardiya", "Açılış Tarihi", "Kapatma Tarihi",
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
# VERİTABANI BAŞLATMA
# =============================================================================

def veritabani_hazirla():
    if not os.path.exists(DB_FILE):
        pd.DataFrame(columns=ARIZA_SUTUNLARI).to_csv(DB_FILE, index=False, encoding="utf-8-sig")
    else:
        df = pd.read_csv(DB_FILE, dtype=str)
        for s in ARIZA_SUTUNLARI:
            if s not in df.columns:
                df[s] = ""
        df.to_csv(DB_FILE, index=False, encoding="utf-8-sig")

    if not os.path.exists(STOK_FILE):
        baslangic = {
            "Malzeme Kodu": ["M001","M002","M003","M004","M005","M006","M007","M008"],
            "Malzeme Adı": [
                "VNA Sürüş Tekerleği (225mm)", "RT Mesafe Sensörü (Sick)",
                "PLC Dijital Giriş Modülü (Siemens)", "Rulman (6204-2RS)",
                "Hidrolik Yağ ISO-46", "Konveyör Kayışı (B-1500)",
                "Motor Koruma Sigortası (16A)", "Endüstriyel Filtre Elemanı"
            ],
            "Kategori": ["Hareketli Parça","Sensör","Elektrik","Mekanik","Sarf","Hareketli Parça","Elektrik","Sarf"],
            "Birim": ["Adet","Adet","Adet","Adet","Litre","Metre","Adet","Adet"],
            "Stok Miktarı": [8, 12, 4, 25, 40, 30, 20, 15],
            "Kritik Seviye": [2, 3, 1, 5, 10, 5, 5, 3],
            "Maksimum Stok": [15, 20, 8, 50, 80, 60, 40, 30],
            "Son Fiyat (TL)": [850, 1200, 2400, 45, 180, 95, 35, 220],
            "Tedarikçi": ["Jungheinrich TR","Sick Türkiye","Siemens TR","SKF Türkiye",
                          "Shell TR","ContiTech","ABB TR","Parker TR"],
            "Son Güncelleme": [datetime.now().strftime("%d/%m/%Y")] * 8
        }
        pd.DataFrame(baslangic).to_csv(STOK_FILE, index=False, encoding="utf-8-sig")

    if not os.path.exists(KULLANICI_FILE):
        with open(KULLANICI_FILE, "w", encoding="utf-8") as f:
            json.dump(KULLANICILAR_DEFAULT, f, ensure_ascii=False, indent=2)

    if not os.path.exists(LOG_FILE):
        pd.DataFrame(columns=["Zaman","Kullanıcı","İşlem","Detay"]).to_csv(
            LOG_FILE, index=False, encoding="utf-8-sig"
        )

veritabani_hazirla()

# =============================================================================
# YARDIMCI FONKSİYONLAR
# =============================================================================

def log_yaz(islem: str, detay: str = ""):
    kullanici = st.session_state.get("aktif_kullanici", "Sistem")
    yeni = pd.DataFrame([{
        "Zaman": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "Kullanıcı": kullanici, "İşlem": islem, "Detay": detay
    }])
    df = pd.read_csv(LOG_FILE)
    pd.concat([df, yeni], ignore_index=True).to_csv(LOG_FILE, index=False, encoding="utf-8-sig")

def sla_hesapla(oncelik: str, acilis: str, kapanis: str = None) -> dict:
    sla_dk = ARIZA_ONCELIKLERI.get(oncelik, {}).get("sla_dk", 480)
    try:
        ac = datetime.strptime(acilis, "%d/%m/%Y %H:%M")
        bitis = datetime.strptime(kapanis, "%d/%m/%Y %H:%M") if kapanis and kapanis != "-" else datetime.now()
        gecen = (bitis - ac).total_seconds() / 60
        return {
            "gecen_dk": int(gecen),
            "sla_dk": sla_dk,
            "oran": round(gecen / sla_dk * 100, 1),
            "durum": "✅ SLA İçinde" if gecen <= sla_dk else "⚠️ SLA Aşıldı"
        }
    except:
        return {"gecen_dk": 0, "sla_dk": sla_dk, "oran": 0, "durum": "—"}

def talep_no_uret(df: pd.DataFrame) -> str:
    yil = datetime.now().year
    ay  = datetime.now().month
    prefix = f"ARZ-{yil}{ay:02d}-"
    filtre = df["Talep No"].astype(str).str.startswith(prefix) if len(df) > 0 else pd.Series([], dtype=bool)
    mevcut = df[filtre]["Talep No"].astype(str) if filtre.any() else pd.Series([], dtype=str)
    no = len(mevcut) + 1
    return f"{prefix}{no:03d}"

# =============================================================================
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

# Streamlit'in portal/popover katmanına ulaşmak için JS ile dinamik style enjeksiyonu
st.markdown("""
<script>
(function injectDropdownStyles() {
    const css = `
        /* Dropdown açılır liste */
        [data-baseweb="popover"] { background:#1e293b !important; }
        [data-baseweb="menu"]    { background:#1e293b !important; border:1px solid rgba(99,179,237,0.3) !important; border-radius:8px !important; }
        [data-baseweb="menu"] ul { background:#1e293b !important; padding:4px !important; }
        [data-baseweb="menu"] li { background:#1e293b !important; color:#e2e8f0 !important; border-radius:6px !important; padding:8px 12px !important; }
        [data-baseweb="menu"] li:hover,
        [data-baseweb="menu"] li[aria-selected="true"] { background:#2d4a6e !important; color:#ffffff !important; }
        /* Seçili değer metni */
        [data-baseweb="select"] [data-testid="stMarkdownContainer"],
        [data-baseweb="select"] div { color:#e2e8f0 !important; }
        [data-baseweb="select"] div[class*="ValueContainer"] { background:#0f172a !important; }
        [data-baseweb="select"] div[class*="control"]        { background:#0f172a !important; border-color:rgba(99,179,237,0.25) !important; }
        [data-baseweb="select"] div[class*="singleValue"]    { color:#e2e8f0 !important; }
        [data-baseweb="select"] div[class*="placeholder"]    { color:#64748b !important; }
        [data-baseweb="select"] div[class*="option"]         { background:#1e293b !important; color:#e2e8f0 !important; }
        [data-baseweb="select"] div[class*="option"]:hover   { background:#2d4a6e !important; color:#fff !important; }
        /* Tüm liste öğeleri (role=option) */
        li[role="option"]                        { background:#1e293b !important; color:#e2e8f0 !important; }
        li[role="option"]:hover                  { background:#2d4a6e !important; color:#ffffff !important; }
        li[role="option"][aria-selected="true"]  { background:#1d4ed8 !important; color:#ffffff !important; }
    `;
    const style = document.createElement('style');
    style.textContent = css;
    document.head.appendChild(style);

    // Dinamik olarak açılan popover'ları da yakala
    const observer = new MutationObserver(() => {
        document.querySelectorAll('[data-baseweb="popover"]').forEach(el => {
            el.style.setProperty('background', '#1e293b', 'important');
        });
        document.querySelectorAll('li[role="option"]').forEach(el => {
            el.style.setProperty('background-color', '#1e293b', 'important');
            el.style.setProperty('color', '#e2e8f0', 'important');
        });
    });
    observer.observe(document.body, { childList: true, subtree: true });

    // Canlı saat
    function saatiGuncelle() {
        const el = document.getElementById('canli-saat');
        if (el) {
            const now = new Date();
            const s = now.toLocaleTimeString('tr-TR', {hour:'2-digit', minute:'2-digit', second:'2-digit'});
            el.textContent = s;
        }
    }
    saatiGuncelle();
    setInterval(saatiGuncelle, 1000);
})();
</script>
""", unsafe_allow_html=True)


# =============================================================================
# YETKİLENDİRME SİSTEMİ
# =============================================================================

def kullanicilari_yukle() -> dict:
    try:
        with open(KULLANICI_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return KULLANICILAR_DEFAULT

def sifre_hashle(sifre: str) -> str:
    return hashlib.sha256(sifre.encode()).hexdigest()

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
            </div>
            """, unsafe_allow_html=True)
            components.html("""
            <div id="oturum-saat" style="font-size:11px;color:#475569;
                 padding:0 4px;margin-top:-4px;margin-bottom:6px;">
              --
            </div>
            <script>
              function oturumSaatGuncelle() {
                var el = document.getElementById('oturum-saat');
                if (!el) return;
                var now = new Date();
                var gun = String(now.getDate()).padStart(2,'0');
                var aylar = ['Oca','Şub','Mar','Nis','May','Haz',
                             'Tem','Ağu','Eyl','Eki','Kas','Ara'];
                var ay  = aylar[now.getMonth()];
                var yil = now.getFullYear();
                var s   = String(now.getHours()).padStart(2,'0');
                var d   = String(now.getMinutes()).padStart(2,'0');
                var sn  = String(now.getSeconds()).padStart(2,'0');
                el.textContent = gun + ' ' + ay + ' ' + yil + '  ' + s + ':' + d + ':' + sn;
              }
              oturumSaatGuncelle();
              setInterval(oturumSaatGuncelle, 1000);
            </script>
            """, height=24)
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
        df_sb = pd.read_csv(DB_FILE, dtype=str)
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
    df = pd.read_csv(DB_FILE, dtype=str)

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

    # Her sekme render'ında saati tazele (form açılmadan önce)
    if "bildirim_saat_default" not in st.session_state:
        st.session_state["bildirim_saat_default"] = datetime.now().strftime("%H:%M")
    # Butona basılmadıysa (yani form temizlenmediyse) saati güncelle
    if not st.session_state.get("_talep_gonderildi", False):
        st.session_state["bildirim_saat_default"] = datetime.now().strftime("%H:%M")
    else:
        st.session_state["_talep_gonderildi"] = False

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
            bildirim_saat= st.text_input("Arıza Fark Edilme Saati", value=st.session_state["bildirim_saat_default"], help="SS:DD formatında (örn: 14:30)")

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
                df_c = pd.read_csv(DB_FILE, dtype=str)
                no   = talep_no_uret(df_c)
                yeni = {
                    "Talep No": no, "Durum": "Açık", "Öncelik": oncelik,
                    "Vardiya": vardiya, "Açılış Tarihi": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "Kapatma Tarihi": "", "Bildiren": bildiren.strip(),
                    "Bildiren Departman": bildiren_dept, "Müdahale Eden": "",
                    "Makine": makine, "Arıza Türü": ariza_tur, "Alt Kategori": alt_kategori,
                    "Arıza Tanımı": ariza_tanimi.strip(),
                    "Bildirim Saati": bildirim_saat.strip(),
                    "İlk Müdahale Saati": "", "Çözüm Süresi (Dk)": "",
                    "SLA Durumu": "Açık — Süre Devam Ediyor",
                    "Çözüm Açıklaması": "", "Kök Neden": "", "5 Neden Analizi": "",
                    "Kaizen Önerisi": "", "Kullanılan Malzemeler": "",
                    "Malzeme Maliyeti (TL)": 0, "İş Gücü Maliyeti (TL)": 0,
                    "Toplam Maliyet (TL)": 0, "Fotoğraf Notu": foto_notu,
                    "Kapatma Onayı": ""
                }
                pd.concat([df_c, pd.DataFrame([yeni])], ignore_index=True).to_csv(
                    DB_FILE, index=False, encoding="utf-8-sig"
                )
                log_yaz("YENİ TALEP", f"{no} — {makine} — {bildiren}")
                st.session_state["_talep_gonderildi"] = True
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
        df_k = pd.read_csv(DB_FILE, dtype=str)
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

            # ── MTTR/MTBF yardımcı fonksiyonu
            def mttr_mtbf_hesapla(makine_adi):
                try:
                    df_all = pd.read_csv(DB_FILE, dtype=str)
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
                    if len(df_m) >= 2:
                        farklar  = df_m["kap"].diff().dropna()
                        mtbf_dk  = round(farklar.dt.total_seconds().mean() / 60, 1)
                    else:
                        mtbf_dk  = None
                    return {"mttr": mttr, "mtbf": mtbf_dk, "toplam_ariza": len(df_m)}
                except:
                    return None

            ISCI_SAAT_UCRETI = 300  # TL/saat sabit tarife

            # ── Kapatma Formu
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
                        help="Teknisyenin makinenin başına geçtiği saat (SS:DD)"
                    )
                with col_k3:
                    mudahale_bit_str = st.text_input(
                        "🕑 Arıza Giderilme Saati *",
                        value=datetime.now().strftime("%H:%M"),
                        help="Makinenin tekrar devreye alındığı saat (SS:DD)"
                    )

                # Saatleri parse et
                try:
                    bas_dt = datetime.strptime(
                        date.today().strftime("%d/%m/%Y") + " " + mudahale_bas_str.strip(),
                        "%d/%m/%Y %H:%M"
                    )
                    bit_dt = datetime.strptime(
                        date.today().strftime("%d/%m/%Y") + " " + mudahale_bit_str.strip(),
                        "%d/%m/%Y %H:%M"
                    )
                    if bit_dt < bas_dt:          # gece geçişi
                        bit_dt += timedelta(days=1)
                    cozum_suresi_dk = max(1, int((bit_dt - bas_dt).total_seconds() / 60))
                    saat_parse_ok   = True
                except ValueError:
                    cozum_suresi_dk = 1
                    saat_parse_ok   = False

                isguc_maliyet = round((cozum_suresi_dk / 60) * ISCI_SAAT_UCRETI, 2)

                if not saat_parse_ok:
                    st.warning("⚠️ Saat formatı hatalı. Lütfen **SS:DD** formatında girin (örn: 14:30)")
                else:
                    st.info(
                        f"⏱ **Çözüm Süresi:** {cozum_suresi_dk} dakika "
                        f"({cozum_suresi_dk//60}s {cozum_suresi_dk%60}dk)  —  "
                        f"💰 **Otomatik İş Gücü Maliyeti:** {isguc_maliyet:,.0f} TL "
                        f"(300 TL/saat × {cozum_suresi_dk/60:.2f} saat)"
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

                cozum_aciklama = st.text_area(
                    "Uygulanan Çözüm & Teknik Notlar *",
                    placeholder="Yapılan müdahaleyi detaylı açıklayın.",
                    height=90
                )
                neden_analizi = st.text_area(
                    "5 Neden Analizi",
                    placeholder="Neden 1: ...\nNeden 2: ...\nNeden 3: ...\nNeden 4: ...\nNeden 5: ...",
                    height=100
                )
                kaizen = st.text_area(
                    "Kaizen / İyileştirme Önerisi",
                    placeholder="Arızanın tekrarlanmaması için neler yapılabilir?",
                    height=70
                )

                st.markdown("##### 📦 Kullanılan Malzeme")
                df_stok_k = pd.read_csv(STOK_FILE, dtype=str)
                col_stk1, col_stk2, col_stk3 = st.columns(3)
                with col_stk1:
                    malzeme_secim = st.selectbox(
                        "Stoktan Malzeme",
                        ["—  Malzeme Kullanılmadı"] + df_stok_k["Malzeme Adı"].tolist()
                    )
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
                        malzeme_metni = "—"
                        if "—" not in malzeme_secim and malzeme_adet > 0:
                            stok_mik = int(df_stok_k.loc[
                                df_stok_k["Malzeme Adı"] == malzeme_secim, "Stok Miktarı"
                            ].values[0])
                            if stok_mik < malzeme_adet:
                                st.error(f"❌ Yetersiz stok! Mevcut: {stok_mik} adet")
                                st.stop()
                            yeni_stok = stok_mik - malzeme_adet
                            df_stok_k.loc[df_stok_k["Malzeme Adı"] == malzeme_secim, "Stok Miktarı"] = str(yeni_stok)
                            df_stok_k.loc[df_stok_k["Malzeme Adı"] == malzeme_secim, "Son Güncelleme"] = \
                                datetime.now().strftime("%d/%m/%Y")
                            df_stok_k.to_csv(STOK_FILE, index=False, encoding="utf-8-sig")
                            malzeme_metni = f"{malzeme_secim} x {malzeme_adet}"

                        toplam_maliyet  = isguc_maliyet + malzeme_maliyet
                        kapatma_zaman   = datetime.now().strftime("%d/%m/%Y %H:%M")
                        mudahale_aralik = f"{mudahale_bas_str.strip()} - {mudahale_bit_str.strip()}"
                        sla_s = sla_hesapla(talep["Öncelik"], talep["Açılış Tarihi"], kapatma_zaman)

                        df_k2 = pd.read_csv(DB_FILE, dtype=str)
                        guncelle = {
                            "Durum":                  "Kapalı",
                            "Kapatma Tarihi":         kapatma_zaman,
                            "Müdahale Eden":          mudahale_eden.strip(),
                            "İlk Müdahale Saati":     mudahale_aralik,
                            "Çözüm Süresi (Dk)":      str(cozum_suresi_dk),
                            "SLA Durumu":             sla_s["durum"],
                            "Çözüm Açıklaması":       cozum_aciklama.strip(),
                            "Kök Neden":              str(kok_neden),
                            "5 Neden Analizi":        neden_analizi,
                            "Kaizen Önerisi":         kaizen,
                            "Kullanılan Malzemeler":  malzeme_metni,
                            "Malzeme Maliyeti (TL)":  str(malzeme_maliyet),
                            "İş Gücü Maliyeti (TL)":  str(isguc_maliyet),
                            "Toplam Maliyet (TL)":    str(toplam_maliyet),
                            "Kapatma Onayı":          str(kapatma_onayi),
                        }
                        for sutun, deger in guncelle.items():
                            if sutun in df_k2.columns:
                                df_k2.loc[df_k2["Talep No"] == secilen_no, sutun] = deger
                        df_k2.to_csv(DB_FILE, index=False, encoding="utf-8-sig")
                        log_yaz("TALEP KAPATILDI",
                                f"{secilen_no} - {mudahale_eden} - {cozum_suresi_dk} dk - {toplam_maliyet:.0f} TL")
                        st.success(
                            f"Talep {secilen_no} basariyla kapatildi! "
                            f"Sure: {cozum_suresi_dk} dk ({mudahale_aralik}) | "
                            f"Is Gucu: {isguc_maliyet:,.0f} TL | Toplam: {toplam_maliyet:,.0f} TL | "
                            f"{sla_s['durum']}"
                        )
                        time.sleep(1.5)
                        st.rerun()

            # MTTR / MTBF Paneli
            st.markdown("---")
            st.markdown("#### MTTR & MTBF Analizi - " + talep["Makine"])
            sonuc = mttr_mtbf_hesapla(talep["Makine"])
            if sonuc:
                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("MTTR (Ort. Tamir Suresi)", f"{sonuc['mttr']} dk")
                with col_m2:
                    mtbf_goster = f"{sonuc['mtbf']} dk" if sonuc["mtbf"] else "Yetersiz veri"
                    st.metric("MTBF (Ort. Arizalar Arasi Sure)", mtbf_goster)
                with col_m3:
                    st.metric("Toplam Ariza (Bu Makine)", f"{sonuc['toplam_ariza']} adet")
                if sonuc["mtbf"]:
                    avail = round(sonuc["mtbf"] / (sonuc["mtbf"] + sonuc["mttr"]) * 100, 1)
                    st.success(
                        f"Ekipman Kullanilabilirlik Orani (Availability): %{avail}   "
                        f"= MTBF / (MTBF + MTTR)"
                    )
            else:
                st.info(
                    f"{talep['Makine']} icin henuz yeterli kapanmis ariza verisi yok. "
                    "Ilk talep kapatildiktan sonra MTTR/MTBF hesaplanacak."
                )


# =============================================================================
# SEKME 4: RAPORLAMA & ARŞİV
# =============================================================================

with tab_rapor:
    if not giris_gerektir("Teknisyen"):
        pass
    else:
        st.markdown("### 📋 Arıza Arşivi & Gelişmiş Raporlama")
        df_r = pd.read_csv(DB_FILE, dtype=str)

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
        df_st = pd.read_csv(STOK_FILE)

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
                    df_st2 = pd.read_csv(STOK_FILE, dtype=str)
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

                    df_st2.loc[mask_s, "Stok Miktarı"]  = str(yeni_m)
                    df_st2.loc[mask_s, "Son Güncelleme"] = datetime.now().strftime("%d/%m/%Y")
                    df_st2.to_csv(STOK_FILE, index=False, encoding="utf-8-sig")
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
                        df_st3 = pd.read_csv(STOK_FILE)
                        if y_kod in df_st3["Malzeme Kodu"].values:
                            st.error("Bu kod zaten mevcut!")
                        else:
                            yeni_s = {
                                "Malzeme Kodu": y_kod, "Malzeme Adı": y_ad.strip(),
                                "Kategori": y_kat, "Birim": y_bir,
                                "Stok Miktarı": y_stok, "Kritik Seviye": y_krit,
                                "Maksimum Stok": y_maks, "Son Fiyat (TL)": y_fiyat,
                                "Tedarikçi": y_tedarik,
                                "Son Güncelleme": datetime.now().strftime("%d/%m/%Y")
                            }
                            pd.concat([df_st3, pd.DataFrame([yeni_s])], ignore_index=True)\
                              .to_csv(STOK_FILE, index=False, encoding="utf-8-sig")
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
                        kullanicilar[duz_secim]["tam_ad"] = duz_tamad.strip() or kullanicilar[duz_secim]["tam_ad"]
                        kullanicilar[duz_secim]["rol"]    = duz_rol
                        if duz_sifre:
                            kullanicilar[duz_secim]["sifre"] = sifre_hashle(duz_sifre)
                        with open(KULLANICI_FILE, "w", encoding="utf-8") as f:
                            json.dump(kullanicilar, f, ensure_ascii=False, indent=2)
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
                    del kullanicilar[sil_secim]
                    with open(KULLANICI_FILE, "w", encoding="utf-8") as f:
                        json.dump(kullanicilar, f, ensure_ascii=False, indent=2)
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
                        kullanicilar[y_kullanici.lower()] = {
                            "sifre": sifre_hashle(y_sifre),
                            "rol": y_rol, "tam_ad": y_tamad
                        }
                        with open(KULLANICI_FILE,"w",encoding="utf-8") as f:
                            json.dump(kullanicilar, f, ensure_ascii=False, indent=2)
                        log_yaz("KULLANICI OLUŞTURULDU", f"{y_kullanici} — {y_rol}")
                        st.success(f"✅ {y_tamad} ({y_rol}) oluşturuldu!")
                        st.rerun()

        with col_a2:
            st.markdown("#### 📜 Sistem Aktivite Logu")
            try:
                df_log = pd.read_csv(LOG_FILE)
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
            except:
                st.info("Henüz aktivite kaydı yok.")

            st.markdown("---")
            st.markdown("#### 🗄️ Veri Yedekleme")
            col_bk1, col_bk2 = st.columns(2)
            with col_bk1:
                if os.path.exists(DB_FILE):
                    with open(DB_FILE,"rb") as f:
                        st.download_button(
                            "💾 Arıza DB Yedeği", f.read(),
                            file_name=f"ariza_db_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                            mime="text/csv", use_container_width=True
                        )
            with col_bk2:
                if os.path.exists(STOK_FILE):
                    with open(STOK_FILE,"rb") as f:
                        st.download_button(
                            "💾 Stok DB Yedeği", f.read(),
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
                    df_t = pd.read_csv(DB_FILE, dtype=str)
                    df_t = df_t[df_t["Durum"] == "Açık"]
                    df_t.to_csv(DB_FILE, index=False, encoding="utf-8-sig")
                    log_yaz("VERİ TEMİZLEME", "Kapalı talepler silindi")
                    st.success("Kapalı talepler temizlendi.")
                    st.rerun()
            with col_d2:
                if st.button("🗑️ Sistem Logunu Temizle", use_container_width=True):
                    pd.DataFrame(columns=["Zaman","Kullanıcı","İşlem","Detay"])\
                      .to_csv(LOG_FILE, index=False, encoding="utf-8-sig")
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
