import streamlit as st
import requests
from datetime import datetime, timedelta

def main():
    st.title("Tekne Fiyat Takip Sistemi")
    
    # Sidebar - Bot Kontrolü
    st.sidebar.title("Bot Kontrolü")
    if st.sidebar.button("Bot'u Başlat"):
        response = requests.post("http://localhost:8000/api/bot/start")
        st.sidebar.success("Bot başlatıldı!")
    
    if st.sidebar.button("Bot'u Durdur"):
        response = requests.post("http://localhost:8000/api/bot/stop")
        st.sidebar.error("Bot durduruldu!")
    
    # Ana Sayfa - Fiyat Analizi
    st.header("Fiyat Analizi")
    
    # Tarih Aralığı Seçimi
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Başlangıç Tarihi")
    with col2:
        end_date = st.date_input("Bitiş Tarihi")
    
    # Rakip Firma Seçimi
    competitors = ["Rudder&Moor", "Diğer Firma 1", "Diğer Firma 2"]
    selected_competitor = st.multiselect("Rakip Firmalar", competitors)
    
    if st.button("Fiyatları Analiz Et"):
        # API'den veri çekme simülasyonu
        st.info("Veriler yükleniyor...")
        
        # Örnek veri gösterimi
        import pandas as pd
        import plotly.express as px
        
        # Örnek veri
        data = {
            'Tarih': pd.date_range(start_date, end_date),
            'Bizim Fiyat': [1000, 1200, 1100, 900],
            'Rakip Fiyat': [950, 1150, 1050, 920]
        }
        df = pd.DataFrame(data)
        
        # Grafik
        fig = px.line(df, x='Tarih', y=['Bizim Fiyat', 'Rakip Fiyat'],
                     title='Fiyat Karşılaştırması')
        st.plotly_chart(fig)
        
        # Fiyat Farkları Tablosu
        st.subheader("Fiyat Farkları")
        st.dataframe(df)

if __name__ == "__main__":
    main() 