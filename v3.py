# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# --- 1. VERİ TABANI VE YETKİLENDİRME AYARLARI ---
DB_FILE = "ariza_kayitlari.csv"

# Yetkili Kullanıcı Listesi
YETKILI_KULLANICILAR = {
    "sezer": "1905",
    "teknik_admin": "1905",
    "mudur": "1905"
}

def veritabani_hazirla():
    sutunlar = [
        "Talep No", "Durum", "Arıza Öncelik", "Vardiya No", "Kayıt Tarihi", "Kapatma Tarihi", 
        "Bildiren", "Müdahale Eden", "Makine/Sistem", "Arıza Türü", "Arıza Tanımı", 
        "Bildirim Saati", "Müdahale Zamanı", "Süre (Dk)", "Çözüm", "Kök Neden (5 Why)", "Kaizen Önerisi", "Malzemeler"
    ]
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=sutunlar)
        df.to_csv(DB_FILE, index=False, encoding="utf-8-sig")
    else:
        df = pd.read_csv(DB_FILE)
        for sutun in sutunlar:
            if sutun not in df.columns:
                df[sutun] = "-"
        df.to_csv(DB_FILE, index=False, encoding="utf-8-sig")

veritabani_hazirla()

# --- 2. ARAYÜZ VE GÖRSEL (CSS) AYARLARI ---
st.set_page_config(page_title="Teknik Bakım & Talep Yönetimi", layout="wide")

st.markdown("""
    <style>
        .stApp { background-color: #FFFF00 !important; }
        h1, h2, h3, p, label, .stMarkdown, .stText { color: #800080 !important; }
        input, textarea, select { color: #800080 !important; }
        button[data-baseweb="tab"] { color: #800080 !important; }
        div[data-testid="stForm"] {
            background-color: #FFFFE0 !important;
            border: 2px solid #800080 !important;
            border-radius: 10px;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🛠️ Teknik Ekip Gelişmiş Arıza & Operasyon Yönetim Sistemi")

# Sayfaları sekmeler halinde ayırıyoruz
sekme_talep_ac, sekme_talep_kapat, sekme_rapor = st.tabs([
    "➕ Yeni Arıza Talebi Aç", 
    "✅ Açık Talepleri Kapat (Giriş Gerekli)", 
    "📋 Gelişmiş Raporlama Arşivi (Giriş Gerekli)"
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
            ariza_turu = st.selectbox("Arıza Kategorisi", ["Elektrik", "Mekanik", "Tesisat", "İstif Makineleri"])
        with col2:
            ariza_onceligi = st.selectbox("Arıza Kritiklik Seviyesi (SLA)", ["🔴 Yüksek (Sistem Durdu)", "🟡 Orta (Sistem Yavaş)", "🔵 Düşük (Planlı Bakım)"])
            vardiya_no = st.selectbox("Mevcut Vardiya", ["Vardiya 1 (08:00 - 16:00)", "Vardiya 2 (16:00 - 00:00)", "Vardiya 3 (00:00 - 08:00)"])
            bildirim_saati = st.time_input("Arıza Fark Edilme Saati", datetime.now().time())
            
        ariza_detayi = st.text_input("Arıza Tanımı (Kısa Özeti)")
        submit_ac = st.form_submit_button("Arıza Talebi Oluştur")
        
        if submit_ac:
            df_current = pd.read_csv(DB_FILE)
            yeni_id = len(df_current) + 1
            
            yeni_talep = {
                "Talep No": yeni_id, "Durum": "Açık", "Arıza Öncelik": ariza_onceligi, "Vardiya No": vardiya_no,
                "Kayıt Tarihi": datetime.now().strftime("%d/%m/%Y %H:%M"), "Kapatma Tarihi": "-",
                "Bildiren": bildiren, "Müdahale Eden": "-", "Makine/Sistem": secilen_makine,
                "Arıza Türü": ariza_turu, "Arıza Tanımı": ariza_detayi, 
                "Bildirim Saati": bildirim_saati.strftime("%H:%M"), "Müdahale Zamanı": "-",
                "Süre (Dk)": 0, "Çözüm": "-", "Kök Neden (5 Why)": "-", "Kaizen Önerisi": "-", "Malzemeler": "-"
            }
            
            df_updated = pd.concat([df_current, pd.DataFrame([yeni_talep])], ignore_index=True)
            df_updated.to_csv(DB_FILE, index=False, encoding="utf-8-sig")
            st.success(f"Talep No #{yeni_id} başarıyla açıldı!")

# --- KULLANICI DOĞRULAMA (LOGIN) FONKSİYONU ---
def kullanici_giris_kontrol(sayfa_anahtari):
    if "oturum_acildi" not in st.session_state:
        st.session_state.oturum_acildi = False
        st.session_state.aktif_kullanici = ""

    if not st.session_state.oturum_acildi:
        st.warning("🔒 Bu bölüme erişmek için kullanıcı adı ve şifrenizle giriş yapmalısınız.")
        with st.form(f"giris_formu_{sayfa_anahtari}"):
            kullanici_adi = st.text_input("Kullanıcı Adı", key=f"user_{sayfa_anahtari}").strip().lower()
            sifre = st.text_input("Şifre", type="password", key=f"pass_{sayfa_anahtari}")
            giris_butonu = st.form_submit_button("Giriş Yap")
            
            if giris_butonu:
                if kullanici_adi in YETKILI_KULLANICILAR and YETKILI_KULLANICILAR[kullanici_adi] == sifre:
                    st.session_state.oturum_acildi = True
                    st.session_state.aktif_kullanici = kullanici_adi
                    st.success(f"Hoş geldiniz, {kullanici_adi.capitalize()}!")
                    st.rerun()
                else:
                    st.error("Hatalı Kullanıcı Adı veya Şifre! Lütfen tekrar deneyin.")
        return False
    
    if st.button(f"🚪 Çıkış Yap ({st.session_state.aktif_kullanici.capitalize()})", key=f"cikis_{sayfa_anahtari}"):
        st.session_state.oturum_acildi = False
        st.session_state.aktif_kullanici = ""
        st.rerun()
    return True

# --- 4. SEKME: TALEP KAPATMA ---
with sekme_talep_kapat:
    if kullanici_giris_kontrol("kapatma_sayfasi"):
        df_current = pd.read_csv(DB_FILE)
        acik_talepler = df_current[df_current["Durum"] == "Açık"]
        
        kritik_talepler = acik_talepler[acik_talepler["Arıza Öncelik"].str.contains("Yüksek", na=False)]
        if not kritik_talepler.empty:
            st.error(f"🚨 **DİKKAT:** Şu an sistemde müdahale edilmeyi bekleyen **{len(kritik_talepler)}** adet ÜRETİM DURDURUCU (Kritik) arıza bulunmaktadır!")
            
        st.subheader("Müdahale Edilmeyi Bekleyen Açık Talepler")
        
        if acik_talepler.empty:
            st.info("Harika! Şu anda sistemde açık arıza talebi bulunmuyor.")
        else:
            talep_secenekleri = acik_talepler.apply(lambda r: f"No: {r['Talep No']} - {r['Arıza Öncelik']} - {r['Makine/Sistem']} ({r['Arıza Tanımı']})", axis=1).tolist()
            secilen_talep_str = st.selectbox("Kapatılacak Talebi Seçin", talep_secenekleri)
            
            secilen_id = int(secilen_talep_str.split(" - ")[0].replace("No: ", ""))
            talep_detay = df_current[df_current["Talep No"] == secilen_id].iloc[0]
            
            st.write("---")
            st.warning(f"Seçilen Talep Detayı: **{talep_detay['Bildiren']}** tarafından **{talep_detay['Kayıt Tarihi']}** tarihinde **{talep_detay['Vardiya No']}** esnasında açılmış.")
            
            with st.form("talep_kapat_formu"):
                col1, col2 = st.columns(2)
                with col1:
                    mudahale_eden = st.text_input("Müdahale Eden Teknisyen", value=st.session_state.aktif_kullanici.capitalize())
                    mudahale_zamani = st.text_input("Müdahale Saat Aralığı", placeholder="Örn: 14:00 - 14:45")
                with col2:
                    mudahale_suresi = st.number_input("Toplam Müdahale Süresi (Dakika)", min_value=1, step=1)
                
                cozum_detayi = st.text_area("Uygulanan Çözüm / Teknik Notlar")
                kok_neden = st.text_area("5 Neden Analizi (Arıza Negen Gerçekleşti? Kök Neden)", placeholder="Örn: Rulman yağsız kaldığı için sıkışmış...")
                kaizen_onerisi = st.text_area("Kaizen Önerisi (Arızanın Tekrarlanmaması İçin Ne Yapılmalı?)", placeholder="Örn: Haftalık kontrol listesine eklenmeli...")
                malzemeler_kullanilan = st.text_area("Kullanılan Malzemeler", placeholder="Parça ve adet belirtiniz...")
                
                submit_kapat = st.form_submit_button("Talebi TPM Standartlarında Kapat")
                
                if submit_kapat:
                    df_current.loc[df_current["Talep No"] == secilen_id, [
                        "Durum", "Kapatma Tarihi", "Müdahale Eden", "Müdahale Zamanı", 
                        "Süre (Dk)", "Çözüm", "Kök Neden (5 Why)", "Kaizen Önerisi", "Malzemeler"
                    ]] = [
                        "Kapalı", datetime.now().strftime("%d/%m/%Y %H:%M"), mudahale_eden, mudahale_zamani, 
                        mudahale_suresi, cozum_detayi, kok_neden, kaizen_onerisi, malzemeler_kullanilan
                    ]
                    df_current.to_csv(DB_FILE, index=False, encoding="utf-8-sig")
                    st.success(f"Talep No #{secilen_id} başarıyla kapatıldı!")
                    st.rerun()

# --- 5. SEKME: GELİŞMİŞ RAPORLAMA ARŞİVİ (TARİH FİLTRELİ SÜRÜM) ---
with sekme_rapor:
    if kullanici_giris_kontrol("rapor_sayfasi"):
        st.subheader("📋 Gelişmiş Arıza Arşivi & Akıllı Filtreleme")
        
        if os.path.exists(DB_FILE):
            veriler = pd.read_csv(DB_FILE)
            
            st.write("### 🔍 Akıllı Endüstriyel Süzgeçler")
            
            # Kategori Süzgeçleri Üst Satırda
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                f_oncelik = st.selectbox("Öncelik Seviyesi Süzgeci", ["Tüm Öncelikler", "🔴 Yüksek (Sistem Durdu)", "🟡 Orta (Sistem Yavaş)", "🔵 Düşük (Planlı Bakım)"])
            with col_f2:
                f_vardiya = st.selectbox("Vardiya Süzgeci", ["Tüm Vardiyalar", "Vardiya 1 (08:00 - 16:00)", "Vardiya 2 (16:00 - 00:00)", "Vardiya 3 (00:00 - 08:00)"])
            with col_f3:
                f_durum = st.selectbox("Durum Süzgeci", ["Tüm Kayıtlar", "Açık", "Kapalı"])
            
            # YENİ: Tarih Süzgeçleri Alt Satırda
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                bas_tarih = st.date_input("Başlangıç Tarihi", date(2026, 1, 1)) # Varsayılan olarak 2026 başı
            with col_t2:
                bit_tarih = st.date_input("Bitiş Tarihi", datetime.now().date()) # Varsayılan olarak bugün
                
            # --- FİLTRELEME MANTIĞI ---
            gosterilecek_veri = veriler.copy()
            
            # 1. Kategori Bazlı Filtrelemeler
            if f_oncelik != "Tüm Öncelikler":
                gosterilecek_veri = gosterilecek_veri[gosterilecek_veri["Arıza Öncelik"] == f_oncelik]
            if f_vardiya != "Tüm Vardiyalar":
                gosterilecek_veri = gosterilecek_veri[gosterilecek_veri["Vardiya No"] == f_vardiya]
            if f_durum != "Tüm Kayıtlar":
                gosterilecek_veri = gosterilecek_veri[gosterilecek_veri["Durum"] == f_durum]
            
            # 2. Tarih Bazlı Zaman Aralığı Filtrelemesi
            if bas_tarih > bit_tarih:
                st.error("Hata: Başlangıç tarihi bitiş tarihinden büyük olamaz!")
            else:
                # CSV'deki metin biçimli tarihi geçici olarak sorgulama için sadece 'tarih' formatına çeviriyoruz
                gosterilecek_veri["Gecici_Tarih"] = pd.to_datetime(gosterilecek_veri["Kayıt Tarihi"], format="%d/%m/%Y %H:%M").dt.date
                
                # İki tarih arasında kalanları süzüyoruz
                tarih_maskesi = (gosterilecek_veri["Gecici_Tarih"] >= bas_tarih) & (gosterilecek_veri["Gecici_Tarih"] <= bit_tarih)
                gosterilecek_veri = gosterilecek_veri[tarih_maskesi]
                
                # Temizlik: Geçici oluşturulan sütunu kullanıcı görmesin diye siliyoruz
                gosterilecek_veri = gosterilecek_veri.drop(columns=["Gecici_Tarih"])
                
            st.info(f"📊 Seçilen kriterlere ve tarih aralığına uyan toplam **{len(gosterilecek_veri)}** kayıt listelenmektedir.")
            
            # CSV İndirme Butonu
            csv_data = gosterilecek_veri.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button(
                label="📥 Seçili Raporu İndir (CSV)",
                data=csv_data,
                file_name=f"teknik_tarihli_rapor_{datetime.now().strftime('%d_%m_%Y')}.csv",
                mime="text/csv"
            )
            
            st.dataframe(gosterilecek_veri.sort_index(ascending=False), use_container_width=True)
