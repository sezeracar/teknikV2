# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import io

# --- 1. VERİ TABANI AYARLARI ---
# Verilerin saklanacağı dosya adı
DB_FILE = "ariza_kayitlari.csv"

# Uygulama ilk kez çalışıyorsa veya dosya yoksa sütunları oluştur
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
st.set_page_config(page_title="Bakım Yönetim Sistemi V3", layout="wide")
st.title("🛠️ Teknik Ekip Arıza & Makine Takip Sistemi")

# Veri Giriş Formu
with st.form("teknik_form", clear_on_submit=True):
    st.subheader("Yeni Müdahale Kaydı")
    
    # Ekranı 3 sütuna bölerek alanı verimli kullanıyoruz
    ust_sol, ust_orta, ust_sag = st.columns(3)
    
    with ust_sol:
        bildiren = st.text_input("Arızayı Bildiren")
        mudahale_eden = st.text_input("Müdahale Eden")
        
    with ust_orta:
        # İstediğin makine ve sistem listesi
        makine_listesi = ["VNA1", "VNA2", "VNA3", "RT1", "RT2", "Diğer"]
        secilen_makine = st.selectbox("Müdahale Edilen Makine/Sistem", makine_listesi)
        ariza_turu = st.selectbox("Arıza Türü", ["Elektrik", "Mekanik", "Tesisat", "İstif Makineleri"])
        
    with ust_sag:
        bildirim_saati = st.time_input("Bildirim Saati", datetime.now().time())
        mudahale_zamani = st.text_input("Müdahale Saat Aralığı", placeholder="Örn: 09:15 - 10:00")
        mudahale_suresi = st.number_input("Süre (Dakika)", min_value=1, step=1)

    st.divider() # Görsel ayırıcı çizgi
    
    alt_sol, alt_sag = st.columns(2)
    with alt_sol:
        ariza_tanimi = st.text_input("Arıza Nedir?")
        cozum_notu = st.text_area("Nasıl Çözüldü?")
    with alt_sag:
        malzemeler = st.text_area("Kullanılan Malzemeler", placeholder="Parça ve adet bilgisi...")

    kaydet_butonu = st.form_submit_button("Sisteme Kaydet")

# --- 3. VERİ KAYIT VE EXCEL İŞLEMLERİ ---
if kaydet_butonu:
    yeni_veri = {
        "Kayıt Tarihi": datetime.now().strftime("%d/%m/%Y %H:%M"),
        "Bildiren": bildiren,
        "Müdahale Eden": mudahale_eden,
        "Makine/Sistem": secilen_makine,
        "Arıza Türü": ariza_turu,
        "Arıza Tanımı": ariza_tanimi,
        "Bildirim Saati": bildirim_saati.strftime("%H:%M"),
        "Müdahale Zamanı": mudahale_zamani,
        "Süre (Dk)": mudahale_suresi,
        "Çözüm": cozum_notu,
        "Malzemeler": malzemeler
    }
    
    # CSV'ye ekleme yap
    mevcut_df = pd.read_csv(DB_FILE)
    guncel_df = pd.concat([mevcut_df, pd.DataFrame([yeni_veri])], ignore_index=True)
    guncel_df.to_csv(DB_FILE, index=False, encoding="utf-8-sig")
    st.success(f"{secilen_makine} için arıza kaydı başarıyla oluşturuldu!")

# Verileri Göster ve İndir
st.divider()
veriler = pd.read_csv(DB_FILE)

c1, c2 = st.columns([5, 1])
with c1:
    st.subheader("📋 Kayıt Geçmişi")
with c2:
    # Excel oluşturma
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        veriler.to_excel(writer, index=False, sheet_name='BakimKayitlari')
    
    st.download_button(
        label="📥 Excel İndir",
        data=output.getvalue(),
        file_name="teknik_ekip_rapor.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

st.dataframe(veriler.sort_index(ascending=False), use_container_width=True)