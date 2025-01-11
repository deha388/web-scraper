import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
from mock_data import generate_mock_prices, get_mock_boats
import pandas as pd
import requests
from config import API_URL, TEST_USER

def render_platform_page(platform_name):
    st.title(f"{platform_name} Fiyat Takip Sistemi")
    
    # Bot Kontrolü
    st.sidebar.header("Bot Kontrolü")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button(f"🟢 {platform_name}\nBaşlat", use_container_width=True):
            try:
                response = requests.post(
                    f"{API_URL}/api/{platform_name.lower()}/start",
                    headers={"Authorization": f"Bearer {st.session_state['token']}"}
                )
                if response.status_code == 200:
                    st.success(f"{platform_name} botu başlatıldı!")
            except Exception as e:
                st.error(f"Hata: {str(e)}")
    
    with col2:
        if st.button(f"🔴 {platform_name}\nDurdur", use_container_width=True):
            try:
                response = requests.post(
                    f"{API_URL}/api/{platform_name.lower()}/stop",
                    headers={"Authorization": f"Bearer {st.session_state['token']}"}
                )
                if response.status_code == 200:
                    st.error(f"{platform_name} botu durduruldu!")
            except Exception as e:
                st.error(f"Hata: {str(e)}")

    # Üst Metrikler
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Aktif Takip", value="3 Rakip")
    with col2:
        st.metric(label="Haftalık Ort. Fark", value="€150", delta="-30")
    with col3:
        st.metric(label="En Düşük Fiyat", value="€950", delta="-100")
    with col4:
        st.metric(label="Son Güncelleme", value="5 dk önce")

    # Hafta Seçimi
    st.header("Haftalık Fiyat Analizi")
    
    # Haftalık tarih aralıkları oluştur
    current_date = datetime.now()
    start_of_week = current_date - timedelta(days=current_date.weekday())
    weeks = []
    for i in range(12):
        week_start = start_of_week - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        weeks.append({
            'label': f"{week_start.strftime('%d.%m.%Y')} - {week_end.strftime('%d.%m.%Y')}",
            'start': week_start,
            'end': week_end
        })
    
    selected_week = st.selectbox(
        "Hafta Seçimi",
        options=weeks,
        format_func=lambda x: x['label'],
        key=f"{platform_name}_week"
    )

    # Mock Veri - Haftalık
    df = generate_mock_prices(
        start_date=selected_week['start'],
        end_date=selected_week['end']
    )
    
    # Grafik
    fig = px.line(df, x='date', y=['price', 'our_price'],
                  color='competitor',
                  title=f'Haftalık Fiyat Karşılaştırması ({selected_week["label"]})',
                  labels={'price': 'Rakip Fiyat', 'our_price': 'Bizim Fiyat'})
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detaylı Tablo ve Filtreler
    st.header("Detaylı Fiyat Karşılaştırması")
    
    with st.expander("Filtreler", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            # Tekne Seçimi
            selected_boats = st.multiselect(
                "Tekneler",
                options=[boat["name"] for boat in get_mock_boats()],
                default=[],
                key=f"{platform_name}_boats_filter"
            )
        with col2:
            # Rakip Firma Filtresi
            competitors = ['Hepsi'] + list(df['competitor'].unique())
            selected_competitors = st.multiselect(
                "Rakip Firmalar",
                options=competitors,
                default=['Hepsi']
            )
        with col3:
            # Fiyat Farkı Durumu Filtresi
            status_options = ['Hepsi', '🔴 Yüksek', '🟡 Normal', '🟢 Uygun']
            selected_status = st.multiselect(
                "Fiyat Durumu",
                options=status_options,
                default=['Hepsi']
            )
        with col4:
            # Hafta Filtresi
            selected_weeks = st.multiselect(
                "Haftalar",
                options=[week['label'] for week in weeks],
                default=[selected_week['label']],
                key=f"{platform_name}_weeks_filter"
            )

    # Tüm haftalık verileri getir
    all_weekly_data = generate_mock_prices_for_all_weeks(
        start_date=weeks[-1]['start'],  # En eski hafta
        end_date=weeks[0]['end']        # En yeni hafta
    )
    
    # Fiyat farkı ve durum hesaplama
    all_weekly_data['price_diff'] = all_weekly_data['our_price'] - all_weekly_data['price']
    all_weekly_data['status'] = all_weekly_data['price_diff'].apply(
        lambda x: '🔴 Yüksek' if x > 50 else '🟢 Uygun' if x < -50 else '🟡 Normal'
    )
    
    # Filtreleri uygula
    filtered_df = filter_weekly_data(
        all_weekly_data,
        selected_competitors,
        selected_status,
        selected_weeks
    )
    
    # Haftalık verileri göster
    if not filtered_df.empty:
        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                'week': st.column_config.DateColumn('Hafta'),
                'competitor': 'Rakip Firma',
                'price': st.column_config.NumberColumn(
                    'Rakip Fiyat',
                    format="€%.2f"
                ),
                'our_price': st.column_config.NumberColumn(
                    'Bizim Fiyat',
                    format="€%.2f"
                ),
                'price_diff': st.column_config.NumberColumn(
                    'Fiyat Farkı',
                    format="€%.2f"
                ),
                'status': 'Durum'
            }
        )
        
        # İstatistikler
        st.subheader("Özet İstatistikler")
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_price_diff = filtered_df['price_diff'].mean()
            st.metric(
                "Ortalama Fiyat Farkı",
                f"€{avg_price_diff:.2f}",
                delta=f"€{avg_price_diff:.2f}"
            )
        with col2:
            high_price_count = len(filtered_df[filtered_df['status'] == '🔴 Yüksek'])
            st.metric("Yüksek Fiyatlı Hafta Sayısı", high_price_count)
        with col3:
            low_price_count = len(filtered_df[filtered_df['status'] == '🟢 Uygun'])
            st.metric("Uygun Fiyatlı Hafta Sayısı", low_price_count)
    else:
        st.warning("Seçilen filtrelere uygun veri bulunamadı.")

# Mock data generator'ı güncelle
def generate_mock_prices_for_all_weeks(start_date, end_date):
    """Belirtilen tarih aralığındaki tüm haftalar için veri üret"""
    all_data = []
    current_date = start_date
    
    while current_date <= end_date:
        week_end = current_date + timedelta(days=6)
        weekly_data = generate_mock_prices(current_date, week_end)
        
        # Hafta bilgisini ekle
        weekly_data['week'] = current_date
        
        all_data.append(weekly_data)
        current_date += timedelta(days=7)
    
    return pd.concat(all_data, ignore_index=True)

def filter_weekly_data(df, selected_competitors, selected_status, selected_weeks):
    """Verileri seçilen filtrelere göre filtrele"""
    filtered_df = df.copy()
    
    # Rakip firma filtresi
    if 'Hepsi' not in selected_competitors:
        filtered_df = filtered_df[filtered_df['competitor'].isin(selected_competitors)]
    
    # Durum filtresi
    if 'Hepsi' not in selected_status:
        filtered_df = filtered_df[filtered_df['status'].isin(selected_status)]
    
    # Hafta filtresi
    if selected_weeks:
        filtered_df = filtered_df[filtered_df['week'].isin(selected_weeks)]
    
    return filtered_df.sort_values(['week', 'competitor'], ascending=[False, True])

def login_page():
    st.markdown(
        """
        <style>
        .login-container {
            max-width: 400px;
            margin: 0 auto;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            background: white;
        }
        
        .login-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .stButton > button {
            width: 100%;
        }

        .test-credentials {
            margin-top: 1rem;
            padding: 1rem;
            background: #f0f2f6;
            border-radius: 5px;
            font-size: 0.9em;
            color: #666;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    st.markdown('<div class="login-header">', unsafe_allow_html=True)
    st.title("⛵ Fiyat Takip Sistemi")
    st.markdown("</div>", unsafe_allow_html=True)
    
    email = st.text_input("Email", value=TEST_USER["email"])
    password = st.text_input("Şifre", type="password", value=TEST_USER["password"])
    
    if st.button("Giriş Yap"):
        # Backend bağlantısı olmadığı için test kullanıcı kontrolü
        if email == TEST_USER["email"] and password == TEST_USER["password"]:
            st.session_state["token"] = "test_token_123"  # Dummy token
            st.session_state["is_logged_in"] = True
            st.rerun()
        else:
            st.error("Geçersiz email veya şifre!")
    
    # Test bilgilerini göster
    st.markdown(
        f"""
        <div class="test-credentials">
            <b>Test Kullanıcı Bilgileri:</b><br>
            Email: {TEST_USER["email"]}<br>
            Şifre: {TEST_USER["password"]}
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown("</div>", unsafe_allow_html=True)

def init_session_state():
    if "is_logged_in" not in st.session_state:
        st.session_state["is_logged_in"] = False
    if "token" not in st.session_state:
        st.session_state["token"] = None

def main():
    st.set_page_config(
        page_title="Tekne Fiyat Takip Sistemi",
        page_icon="⛵",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    init_session_state()
    
    if not st.session_state["is_logged_in"]:
        login_page()
        return

    # Sidebar
    with st.sidebar:
        st.title("⛵ Fiyat Takip")
        st.caption("Tekne Kiralama Fiyat Analizi")
        
        # Platform Seçimi
        platform = st.radio(
            "Platform Seçimi",
            ["Nausys", "MMK Booking"],
            key="platform_selection"
        )
        
        st.divider()
        
        # Boş container ile çıkış butonunu aşağı it
        st.empty()
        st.empty()
        st.empty()
        
        # Çıkış Yap butonu en altta
        st.markdown("---")
        if st.button("🚪 Çıkış Yap", use_container_width=True):
            st.session_state["is_logged_in"] = False
            st.session_state["token"] = None
            st.rerun()
    
    # Seçilen platforma göre sayfayı render et
    render_platform_page(platform)

if __name__ == "__main__":
    main() 