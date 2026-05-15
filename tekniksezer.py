# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. VERİ TABANI AYARLARI ---
DB_FILE = "ariza_kayitlari.csv"

def veritabani_hazirla():
    # Dosya yoksa sütun başlıklarıyla birlikte sıfırdan oluşturur
    sutunlar = [
        "Kayıt Tarihi", "Bildiren", "Müdahale Eden", "Makine/Sistem", 
        "Arıza Türü", "Arıza Tanımı", "Bildirim Saati", 
        "Müdahale Zamanı", "Süre (Dk)", "Çözüm", "Malzemeler"
    ]
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=sutunlar)
        df.to_csv(DB_FILE, index=False, encoding="utf-8-sig")

veritabani_hazirla()

# --- 2. ARAYÜZ TASARIMI ---
st.set_page_config(page_title="Teknik Bakım Sistemi", layout="wide")
st.title("🛠️ Teknik Ekip Arıza Takip Sistemi")

# --- 3. VERİ GİRİŞ FORMU ---
with st.form("ariza_formu", clear_on_submit=True):
    st.subheader("Yeni Arıza & Müdahale Kaydı")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        bildiren = st.text_input("Arızayı Bildiren")
        mudahale_eden = st.text_input("Müdahale Eden")
    
    with col2:
        makine_listesi = ["VNA1", "VNA2", "VNA3", "RT1", "RT2", "Diğer"]
        secilen_makine = st.selectbox("Makine/Sistem", makine_listesi)
        ariza_turu = st.selectbox("Arıza Türü", ["Elektrik", "Mekanik", "Tesisat", "İstif Makineleri"])
        
    with col3:
        bildirim_saati = st.time_input("Bildirim Saati", datetime.now().time())
        mudahale_zamani = st.text_input("Müdahale Saatleri", placeholder="Örn: 10:00-11:30")
        mudahale_suresi = st.number_input("Süre (Dk)", min_value=1, step=1)

    ariza_detayi = st.text_input("Arıza Nedir?")
    cozum_detayi = st.text_area("Nasıl Çözüldü?")
    malzemeler = st.text_area("Kullanılan Malzemeler")
    
    submit_button = st.form_submit_button("Sisteme Kaydet")

# --- 4. KAYIT VE İNDİRME İŞLEMLERİ ---
if submit_button:
    yeni_kayit = {
        "Kayıt Tarihi": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "Bildiren": bildiren, "Müdahale Eden": mudahale_eden,
        "Makine/Sistem": secilen_makine, "Arıza Türü": ariza_turu,
        "Arıza Tanımı": ariza_detayi, "Bildirim Saati": bildirim_saati.strftime("%H:%M"),
        "Müdahale Zamanı": mudahale_zamani, "Süre (Dk)": mudahale_suresi,
        "Çözüm": cozum_detayi, "Malzemeler": malzemeler
    }
    
    df_current = pd.read_csv(DB_FILE)
    df_updated = pd.concat([df_current, pd.DataFrame([yeni_kayit])], ignore_index=True)
    df_updated.to_csv(DB_FILE, index=False, encoding="utf-8-sig")
    st.success(f"{secilen_makine} kaydı başarıyla eklendi!")

st.divider()

if os.path.exists(DB_FILE):
    veriler = pd.read_csv(DB_FILE)
    
    c1, c2 = st.columns([5, 1])
    with c1:
        st.subheader("📋 Kayıt Geçmişi")
    with c2:
        # KÜTÜPHANE GEREKTİRMEYEN GÜVENLİ İNDİRME
        csv_data = veriler.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
        st.download_button(
            label="📥 Verileri İndir",
            data=csv_data,
            file_name=f"teknik_rapor_{datetime.now().strftime('%d_%m_%Y')}.csv",
            mime="text/csv"
        )
    
    st.dataframe(veriler.sort_index(ascending=False), use_container_width=True)
