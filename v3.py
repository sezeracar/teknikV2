# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. VERİ TABANI AYARLARI ---
DB_FILE = "ariza_kayitlari.csv"
DOGRU_SIFRE = "1905"  # Belirlediğiniz giriş şifresi

def veritabani_hazirla():
    sutunlar = [
        "Talep No", "Durum", "Kayıt Tarihi", "Kapatma Tarihi", 
        "Bildiren", "Müdahale Eden", "Makine/Sistem", 
        "Arıza Türü", "Arıza Tanımı", "Bildirim Saati", 
        "Müdahale Zamanı", "Süre (Dk)", "Çözüm", "Malzemeler"
    ]
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=sutunlar)
        df.to_csv(DB_FILE, index=False, encoding="utf-8-sig")

veritabani_hazirla()

# --- 2. ARAYÜZ TASARIMI VE SAYFALAMA ---
st.set_page_config(page_title="Teknik Bakım & Talep Yönetimi", layout="wide")
st.title("🛠️ Teknik Ekip Arıza & Talep Yönetim Sistemi")

# Sayfaları sekmeler halinde ayırıyoruz
sekme_talep_ac, sekme_talep_kapat, sekme_rapor = st.tabs([
    "➕ Yeni Arıza Talebi Aç", 
    "✅ Açık Talepleri Kapat (Şifreli)", 
    "📋 Tüm Kayıt Geçmişi & İndirme (Şifreli)"
])

# --- 3. SEKME: TALEP AÇMA (HERKESE AÇIK) ---
with sekme_talep_ac:
    st.subheader("Sahadan Yeni Arıza Bildirimi")
    with st.form("talep_ac_formu", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            bildiren = st.text_input("Arızayı Bildiren Personel")
            makine_listesi = ["VNA1", "VNA2", "VNA3", "RT1", "RT2", "Diğer"]
            secilen_makine = st.selectbox("Arızalı Makine/Sistem", makine_listesi)
        with col2:
            ariza_turu = st.selectbox("Arıza Kategorisi", ["Elektrik", "Mekanik", "Tesisat", "İstif Makineleri"])
            bildirim_saati = st.time_input("Arıza Fark Edilme Saati", datetime.now().time())
            
        ariza_detayi = st.text_input("Arıza Tanımı (Kısa Özeti)")
        
        submit_ac = st.form_submit_button("Arıza Talebi Oluştur")
        
        if submit_ac:
            df_current = pd.read_csv(DB_FILE)
            yeni_id = len(df_current) + 1
            
            yeni_talep = {
                "Talep No": yeni_id, "Durum": "Açık",
                "Kayıt Tarihi": datetime.now().strftime("%d/%m/%Y %H:%M"), "Kapatma Tarihi": "-",
                "Bildiren": bildiren, "Müdahale Eden": "-", "Makine/Sistem": secilen_makine,
                "Arıza Türü": ariza_turu, "Arıza Tanımı": ariza_detayi, 
                "Bildirim Saati": bildirim_saati.strftime("%H:%M"), "Müdahale Zamanı": "-",
                "Süre (Dk)": 0, "Çözüm": "-", "Malzemeler": "-"
            }
            
            df_updated = pd.concat([df_current, pd.DataFrame([yeni_talep])], ignore_index=True)
            df_updated.to_csv(DB_FILE, index=False, encoding="utf-8-sig")
            st.success(f"Talep No #{yeni_id} başarıyla açıldı! Teknik ekibe iletildi.")

# --- KORUMALI SAYFALAR İÇİN ŞİFRE KONTROL FONKSİYONU ---
def sifrli_alan_kontrol():
    """Şifre doğruysa True, yanlışsa veya girilmediyse False döner."""
    if "giris_yetkisi" not in st.session_state:
        st.session_state.giris_yetkisi = False

    if not st.session_state.giris_yetkisi:
        st.warning("🔒 Bu bölüme erişmek için yetkili şifresini girmelisiniz.")
        girilen_sifre = st.text_input("Teknik Ekip Şifresi", type="password", key="sifre_alani")
        if st.button("Giriş Yap"):
            if girilen_sifre == DOGRU_SIFRE:
                st.session_state.giris_yetkisi = True
                st.success("Giriş Başarılı!")
                st.rerun()
            else:
                st.error("Hatalı Şifre! Lütfen tekrar deneyin.")
        return False
    return True

# --- 4. SEKME: TALEP KAPATMA (ŞİFRELİ) ---
with sekme_talep_kapat:
    if sifrli_alan_kontrol():
        st.subheader("Müdahale Edilmeyi Bekleyen Açık Talepler")
        df_current = pd.read_csv(DB_FILE)
        acik_talepler = df_current[df_current["Durum"] == "Açık"]
        
        if acik_talepler.empty:
            st.info("Harika! Şu anda sistemde açık arıza talebi bulunmuyor.")
        else:
            talep_secenekleri = acik_talepler.apply(lambda r: f"No: {r['Talep No']} - {r['Makine/Sistem']} ({r['Arıza Tanımı']})", axis=1).tolist()
            secilen_talep_str = st.selectbox("Kapatılacak Talebi Seçin", talep_secenekleri)
            
            secilen_id = int(secilen_talep_str.split(" - ")[0].replace("No: ", ""))
            talep_detay = df_current[df_current["Talep No"] == secilen_id].iloc[0]
            
            st.write("---")
            st.warning(f"Seçilen Talep Detayı: **{talep_detay['Bildiren']}** tarafından **{talep_detay['Kayıt Tarihi']}** tarihinde açılmış.")
            
            with st.form("talep_kapat_formu", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    mudahale_eden = st.text_input("Müdahale Eden Teknisyen")
                    mudahale_zamani = st.text_input("Müdahale Saat Aralığı", placeholder="Örn: 14:00 - 14:45")
                with col2:
                    mudahale_suresi = st.number_input("Toplam Müdahale Süresi (Dakika)", min_value=1, step=1)
                
                cozum_detayi = st.text_area("Uygulanan Çözüm / Teknik Notlar")
                malzemeler_kullanilan = st.text_area("Kullanılan Malzemeler", placeholder="Parça ve adet belirtiniz...")
                
                submit_kapat = st.form_submit_button("Talebi Çözüldü Olarak İşaretle ve Kapat")
                
                if submit_kapat:
                    df_current.loc[df_current["Talep No"] == secilen_id, [
                        "Durum", "Kapatma Tarihi", "Müdahale Eden", 
                        "Müdahale Zamanı", "Süre (Dk)", "Çözüm", "Malzemeler"
                    ]] = [
                        "Kapalı", datetime.now().strftime("%d/%m/%Y %H:%M"), mudahale_eden,
                        mudahale_zamani, mudahale_suresi, cozum_detayi, malzemeler_kullanilan
                    ]
                    df_current.to_csv(DB_FILE, index=False, encoding="utf-8-sig")
                    st.success(f"Talep No #{secilen_id} başarıyla kapatıldı!")
                    st.rerun()

# --- 5. SEKME: RAPORLAMA VE İNDİRME (ŞİFRELİ) ---
with sekme_rapor:
    if sifrli_alan_kontrol():
        st.subheader("📋 Geçmiş Kayıt Arşivi")
        if os.path.exists(DB_FILE):
            veriler = pd.read_csv(DB_FILE)
            
            csv_data = veriler.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="📥 Tüm Verileri İndir (CSV)",
                data=csv_data,
                file_name=f"teknik_bakim_arsiv_{datetime.now().strftime('%d_%m_%Y')}.csv",
                mime="text/csv"
            )
            st.dataframe(veriler.sort_index(ascending=False), use_container_width=True)
