# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

# --- 1. VERİ TABANI VE DOSYA AYARLARI ---
DB_FILE = "ariza_kayitlari.csv"

def veritabani_hazirla():
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
st.set_page_config(page_title="Bakım Yönetim Sistemi", layout="wide")
st.title("🛠️ Teknik Ekip Arıza & Makine Takip Sistemi")

# --- 3. VERİ GİRİŞ FORMU ---
with st.form("teknik_form", clear_on_submit=True):
    st.subheader("Yeni Müdahale Kaydı")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        bildiren = st.text_input("Arızayı Bildiren Kişi")
        mudahale_eden = st.text_input("Müdahale Eden Teknisyen")
    with col2:
        makine_listesi = ["VNA1", "VNA2", "VNA3", "RT1", "RT2", "Diğer"]
        secilen_makine = st.selectbox("Müdahale Edilen Makine", makine_listesi)
        ariza_turu = st.selectbox("Arıza Türü", ["Elektrik", "Mekanik", "Tesisat", "İstif Makineleri"])
    with col3:
        bildirim_saati = st.time_input("Bildirim Saati", datetime.now().time())
        mudahale_zamani = st.text_input("Müdahale Saat Aralığı (Örn: 09:00-10:00)")
        mudahale_suresi = st.number_input("Süre (Dakika)", min_value=1, step=1)

    ariza_tanimi = st.text_input("Arıza Nedir?")
    cozum_notu = st.text_area("Nasıl Çözüldü?")
    malzemeler = st.text_area("Kullanılan Malzemeler")

    kaydet_butonu = st.form_submit_button("Sisteme Kaydet")

# --- 4. KAYIT İŞLEMİ ---
if kaydet_butonu:
    yeni_veri = {
        "Kayıt Tarihi": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "Bildiren": bildiren, "Müdahale Eden": mudahale_eden,
        "Makine/Sistem": secilen_makine, "Arıza Türü": ariza_turu,
        "Arıza Tanımı": ariza_tanimi, "Bildirim Saati": bildirim_saati.strftime("%H:%M"),
        "Müdahale Zamanı": mudahale_zamani, "Süre (Dk)": mudahale_suresi,
        "Çözüm": cozum_notu, "Malzemeler": malzemeler
    }
    mevcut_df = pd.read_csv(DB_FILE)
    guncel_df = pd.concat([mevcut_df, pd.DataFrame([yeni_veri])], ignore_index=True)
    guncel_df.to_csv(DB_FILE, index=False, encoding="utf-8-sig")
    st.success(f"{secilen_makine} kaydı başarıyla eklendi!")

# --- 5. LİSTELEME VE EXCEL ---
# --- 5. LİSTELEME VE EXCEL (GÜNCEL) ---
st.divider()
if os.path.exists(DB_FILE):
    veriler = pd.read_csv(DB_FILE)
    c1, c2 = st.columns([5, 1])
    with c1: st.subheader("📋 Kayıt Geçmişi")
    with c2:
        try:
            import openpyxl
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                veriler.to_excel(writer, index=False, sheet_name='Rapor')
            
            st.download_button(
                label="📥 Excel İndir", 
                data=output.getvalue(), 
                file_name="teknik_rapor.xlsx", 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        except ImportError:
            # Motor yüklenemezse kullanıcıya teknik uyarı verir
            st.error("Excel motoru (openpyxl) eksik. Lütfen requirements.txt dosyasını kontrol edin.")
        except Exception as e:
            st.warning(f"Hazırlanıyor: {e}")
            
    st.dataframe(veriler.sort_index(ascending=False), use_container_width=True)
