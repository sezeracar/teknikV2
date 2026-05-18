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
        "Talep No", "Durum", "Kayıt Tarihi", "Kapatma Tarihi", 
        "Bildiren", "Müdahale Eden", "Makine/Sistem", 
        "Arıza Türü", "Arıza Tanımı", "Bildirim Saati", 
        "Müdahale Zamanı", "Süre (Dk)", "Çözüm", "Malzemeler"
    ]
    if not os.path.exists(DB_FILE):
        df = pd.DataFrame(columns=sutunlar)
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

st.title("🛠️ Teknik Ekip Arıza & Talep Yönetim Sistemi")

# Uygulama Sekmeleri
sekme_talep_ac, sekme_talep_kapat, sekme_rapor, sekme_grafik = st.tabs([
    "➕ Yeni Arıza Talebi Aç", 
    "✅ Açık Talepleri Kapat (Giriş Gerekli)", 
    "📋 Tüm Kayıt Geçmişi & İndirme (Giriş Gerekli)",
    "📊 MTTR & MTBF Grafik Analizi (Giriş Gerekli)"
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
            
            with st.form("talep_kapat_formu"):
                col1, col2 = st.columns(2)
                with col1:
                    mudahale_eden = st.text_input("Müdahale Eden Teknisyen", value=st.session_state.aktif_kullanici.capitalize())
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

# --- 5. SEKME: RAPORLAMA VE İNDİRME ---
with sekme_rapor:
    if kullanici_giris_kontrol("rapor_sayfasi"):
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

# --- 6. SEKME: MTTR & MTBF YERLEŞİK ANALİZ PANELİ ---
with sekme_grafik:
    if kullanici_giris_kontrol("grafik_sayfasi"):
        st.subheader("📊 Tarih Bazlı MTTR ve MTBF Performans Analizi")
        
        if os.path.exists(DB_FILE):
            df_g = pd.read_csv(DB_FILE)
            
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                bas_tarih = st.date_input("Analiz Başlangıç Tarihi", date(2026, 1, 1))
            with col_t2:
                bit_tarih = st.date_input("Analiz Bitiş Tarihi", datetime.now().date())
                
            if bas_tarih > bit_tarih:
                st.error("Hata: Başlangıç tarihi bitiş tarihinden büyük olamaz!")
            else:
                # Tarih dönüşümleri ve filtreleme
                df_g["Kayıt_P_Tarihi"] = pd.to_datetime(df_g["Kayıt Tarihi"], format="%d/%m/%Y %H:%M").dt.date
                mask = (df_g["Kayıt_P_Tarihi"] >= bas_tarih) & (df_g["Kayıt_P_Tarihi"] <= bit_tarih)
                filtrelenmiş_df = df_g[mask]
                
                toplam_gun = (bit_tarih - bas_tarih).days + 1
                toplam_calisma_saati = toplam_gun * 24 # 7/24 çalışma varsayımı
                
                if filtrelenmiş_df.empty:
                    st.info("Seçilen tarih aralığında herhangi bir arıza kaydı bulunamadı.")
                else:
                    kapali_analiz = filtrelenmiş_df[filtrelenmiş_df["Durum"] == "Kapalı"]
                    
                    if kapali_analiz.empty:
                        st.info("Seçilen tarih aralığında kapatılmış arıza bulunmuyor. MTTR/MTBF hesaplanamaz.")
                    else:
                        # Gruplama ve Hesaplamalar
                        makine_grup = kapali_analiz.groupby("Makine/Sistem").agg(
                            Ariza_Sayisi=("Talep No", "count"),
                            Toplam_Mudahale_Suresi=("Süre (Dk)", "sum")
                        ).reset_index()
                        
                        # Metrik formülleri
                        makine_grup["MTTR (Dk)"] = (makine_grup["Toplam_Mudahale_Suresi"] / makine_grup["Ariza_Sayisi"]).round(1)
                        makine_grup["MTBF (Saat)"] = (toplam_calisma_saati / makine_grup["Ariza_Sayisi"]).round(1)
                        
                        st.write("---")
                        g_col1, g_col2 = st.columns(2)
                        
                        with g_col1:
                            st.markdown("### 🕒 Makine Bazlı MTTR (Ortalama Onarım Süresi - Dakika)")
                            # Hata veren kütüphane yerine Streamlit'in kendi yerleşik çubuk grafiği
                            chart_data_mttr = makine_grup.set_index("Makine/Sistem")[["MTTR (Dk)"]]
                            st.bar_chart(chart_data_mttr, y_label="Dakika")
                            st.caption("Düşük MTTR değeri, daha hızlı müdahale ve onarım anlamına gelir.")
                            
                        with g_col2:
                            st.markdown("### 📈 Makine Bazlı MTBF (Arızalar Arası Ortalama Süre - Saat)")
                            # Hata veren kütüphane yerine Streamlit'in kendi yerleşik çubuk grafiği
                            chart_data_mtbf = makine_grup.set_index("Makine/Sistem")[["MTBF (Saat)"]]
                            st.bar_chart(chart_data_mtbf, y_label="Saat")
                            st.caption("Yüksek MTBF değeri, ekipmanın daha seyrek arıza yaptığını ve kararlı olduğunu gösterir.")
                            
                        st.write("---")
                        st.markdown("### 📊 Detaylı Performans Veri Tablosu")
                        st.dataframe(
                            makine_grup[["Makine/Sistem", "Ariza_Sayisi", "MTTR (Dk)", "MTBF (Saat)"]], 
                            use_container_width=True
                        )
