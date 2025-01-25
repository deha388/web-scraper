import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
from mock_data import generate_mock_prices, get_mock_boats
import pandas as pd
import requests
from config import API_URL, TEST_USER
from datetime import datetime, date

API_BASE = "http://localhost:8000/api/v1"
API_SAILAMOR = "http://localhost:8000/api/v1/sailamor"
API_COMPETITOR = "http://localhost:8000/api/v1/competitor"


def fetch_sailamor_yachts(platform_name, headers):
    """
    Tarih değiştiğinde otomatik tetiklenecek.
    Seçilen tarihe göre /sailamor/yachts/names?date_str=... endpoint'inden
    tekneleri çekip st.session_state["our_yacht_list"] içine koyar.
    Diğer seçimleri sıfırlar.
    """
    date_str = st.session_state["selected_date"].strftime("%Y-%m-%d")
    url = f"{API_SAILAMOR}/yachts/names"
    params = {"platform": str(platform_name).lower(), "date_str": date_str}

    try:
        resp = requests.get(url, params=params, headers=headers)
        if resp.ok:
            data = resp.json()
            yachts = data.get("yacht_names", [])
            st.session_state["our_yacht_list"] = yachts
            # Tekne seçimini reset
            # st.session_state["selected_yacht"] = "Seçiniz"
            # Period verilerini reset
            st.session_state["our_periods_raw"] = []
            st.session_state["selected_period_label"] = "Seçiniz"
            # Rakip verilerini de temizleyebiliriz
            st.session_state["competitor_yacht_list"] = []
            st.session_state["selected_competitor_yacht"] = "Seçiniz"
        else:
            st.error("Tekneler alınamadı: " + resp.text)
    except Exception as e:
        st.error(f"fetch_sailamor_yachts hatası: {e}")


def fetch_sailamor_periods(platform_name, headers):
    """
    Bizim tekne seçimi değiştiğinde otomatik tetiklenecek.
    /sailamor/yachts/periods endpoint'ine gidip period listesini çeker.
    """
    selected_yacht = st.session_state["selected_yacht"]
    if selected_yacht == "Seçiniz":
        # Tekne seçilmemiş
        st.session_state["our_periods_raw"] = []
        st.session_state["selected_period_label"] = "Seçiniz"
        return

    date_str = st.session_state["selected_date"].strftime("%Y-%m-%d")
    url = f"{API_SAILAMOR}/yachts/periods"
    params = {
        "platform": str(platform_name).lower(),
        "date_str": date_str,
        "yacht_name": selected_yacht
    }

    try:
        resp = requests.get(url, params=params, headers=headers)
        if resp.ok:
            data = resp.json()
            periods = data.get("periods", [])
            # periods => [{"from": "2025-04-12 17:00:00", "to": "2025-04-19 08:00:00"}, ...]
            st.session_state["our_periods_raw"] = periods
            st.session_state["selected_period_label"] = "Seçiniz"
            # Rakip verilerini de temizlemek isteyebilirsiniz
            st.session_state["competitor_yacht_list"] = []
            st.session_state["selected_competitor_yacht"] = "Seçiniz"
        else:
            st.error("Period alınamadı: " + resp.text)
    except Exception as e:
        st.error(f"fetch_sailamor_periods hatası: {e}")


def fetch_competitor_yachts(platform_name, headers):
    """
    Rakip firma veya period seçimi değiştiğinde otomatik tetiklenecek.
    Seçili period'a göre rakipte aynı period'a sahip yacht_name'leri çeker.
    """
    competitor = st.session_state["selected_competitor"]
    if competitor == "Seçiniz":
        st.session_state["competitor_yacht_list"] = []
        st.session_state["selected_competitor_yacht"] = "Seçiniz"
        return

    # Rakip firma adını DB formatına çevir ("Rudder&Moor" -> "rudder_moor")
    comp_key = competitor.lower().replace("&", "_").replace(" ", "_")

    date_str = st.session_state["selected_date"].strftime("%Y-%m-%d")
    url = f"{API_COMPETITOR}/yachts/names"
    params = {
        "platform": str(platform_name).lower(),
        "competitor": comp_key,
        "date_str": date_str,

    }

    try:
        resp = requests.get(url, params=params, headers=headers)
        if resp.ok:
            data = resp.json()
            c_yachts = data.get("yacht_names", [])
            st.session_state["competitor_yacht_list"] = c_yachts
            st.session_state["selected_competitor_yacht"] = "Seçiniz"
        else:
            st.error("Rakip tekneler alınamadı: " + resp.text)
    except Exception as e:
        st.error(f"fetch_competitor_yachts hatası: {e}")


def get_chosen_period_value():
    """
    Bizim selectbox'ta '2025-04-12 -> 2025-04-19' gibi bir label var;
    Buna karşılık gelen tam datetime'ları (p['from'], p['to']) bulur.
    """
    label = st.session_state["selected_period_label"]
    if label == "Seçiniz":
        return None

    periods_raw = st.session_state["our_periods_raw"]
    # "YYYY-MM-DD -> YYYY-MM-DD" formatında splitted
    # Ama asıl p['from'] "2025-04-12 17:00:00"
    # Biz labelda date[:10] kullandık.
    # Onu yakalayıp periods_raw içinden eşleşeni bulacağız.
    # Kolaylık için biz her selectbox itemına tam data atayabilirdik.
    # Burada string parse da yapabiliriz.

    # Yöntem 1: on_change'te item'a tıklayınca st.session_state'ye tam from/to yazmak
    # Yöntem 2: Metin parse
    # Burada Yöntem 2:
    # "2025-04-12 -> 2025-04-19" -> "2025-04-12", "2025-04-19"
    parts = label.split("->")
    if len(parts) != 2:
        return None
    date_from_str = parts[0].strip()  # "2025-04-12"
    date_to_str = parts[1].strip()  # "2025-04-19"

    # periods_raw => [{"from":"2025-04-12 17:00:00","to":"2025-04-19 08:00:00"}, ...]
    for p in periods_raw:
        if p["from"][:10] == date_from_str and p["to"][:10] == date_to_str:
            # bulduk
            return (p["from"], p["to"])

    return None


def parse_discounted_price(price_str):
    """
    "17.000,00 EUR" gibi bir metni float'a çevirir -> 17000.00
    Noktaları, virgülleri, "EUR" ibaresini temizleyelim.
    """
    # Örnek dönüşümler:
    # "17.000,00 EUR" -> "17000,00 "
    # -> "17000.00" -> float(17000.00)
    tmp = price_str.upper().replace(" EUR", "").replace(".", "").replace(",", ".")
    try:
        return float(tmp)
    except:
        return 0.0


def compare_prices(platform_name, headers):
    """
    "Fiyat Karşılaştır" butonuna basıldığında çağrılır.
    1) Bizim Tekne -> /sailamor/yachts/all_periods
    2) Rakip Tekne -> /competitor/yachts/all_periods
    3) (period_from, period_to) bazında merge
    4) Tabloda "Bizim Konum", "Rakip Konum" sütunlarını göster
    5) "Aradaki Fark" sütununu € ile formatla
    """

    # 1) Gerekli seçimler kontrol
    if (st.session_state["selected_yacht"] == "Seçiniz"
            or st.session_state["selected_competitor"] == "Seçiniz"
            or st.session_state["selected_competitor_yacht"] == "Seçiniz"):
        st.warning("Lütfen tarih, Bizim Tekne, Rakip Firma ve Rakip Tekne seçiniz!")
        return

    # 2) Endpoint'lere istek
    date_str = st.session_state["selected_date"].strftime("%Y-%m-%d")

    # Bizim firma
    url_our = f"{API_SAILAMOR}/yachts/all_periods"
    params_our = {
        "platform": platform_name.lower(),
        "date_str": date_str,
        "yacht_name": st.session_state["selected_yacht"]
    }
    resp_our = requests.get(url_our, params=params_our, headers=headers)
    if not resp_our.ok:
        st.error("Bizim firmada all_periods verisi alınamadı: " + resp_our.text)
        return
    data_our = resp_our.json().get("periods", [])

    # Rakip firma
    comp_key = st.session_state["selected_competitor"].lower().replace("&", "_").replace(" ", "_")
    url_comp = f"{API_COMPETITOR}/yachts/all_periods"
    params_comp = {
        "platform": platform_name.lower(),
        "competitor": comp_key,
        "date_str": date_str,
        "yacht_name": st.session_state["selected_competitor_yacht"]
    }
    resp_comp = requests.get(url_comp, params=params_comp, headers=headers)
    if not resp_comp.ok:
        st.error("Rakip firmada all_periods verisi alınamadı: " + resp_comp.text)
        return
    data_comp = resp_comp.json().get("periods", [])

    df_our = pd.DataFrame(data_our)  # columns: period_from, period_to, location, discounted_price, original_price, ...
    df_comp = pd.DataFrame(
        data_comp)  # columns: period_from, period_to, location, discounted_price, original_price, ...

    if df_our.empty and df_comp.empty:
        st.info("Ne bizde ne rakipte kayıt bulunamadı.")
        return

    # 3) Fiyatları float parse
    def parse_price(s):
        if not isinstance(s, str):
            return 0.0
        s = s.upper().replace(" EUR", "").replace(".", "").replace(",", ".")
        try:
            return float(s)
        except:
            return 0.0

    if not df_our.empty:
        df_our["price_bizim"] = df_our["discounted_price"].apply(parse_price)
    else:
        df_our["price_bizim"] = []

    if not df_comp.empty:
        df_comp["price_rakip"] = df_comp["discounted_price"].apply(parse_price)
    else:
        df_comp["price_rakip"] = []

    # 4) Merge hazırlığı: rename kolonlar
    df_our.rename(columns={
        "period_from": "pf_our",
        "period_to": "pt_our",
        "location": "loc_our"
    }, inplace=True)
    df_comp.rename(columns={
        "period_from": "pf_comp",
        "period_to": "pt_comp",
        "location": "loc_comp"
    }, inplace=True)

    # 5) Merge => (pf_our, pt_our) == (pf_comp, pt_comp)
    merged = pd.merge(
        df_our, df_comp,
        how="inner",  # sadece ortak satırlar
        left_on=["pf_our", "pt_our"],
        right_on=["pf_comp", "pt_comp"],
        suffixes=("_our", "_rakip")
    )

    if merged.empty:
        st.info("Biz ve rakipte eşleşen period bulunamadı!")
        return

    # 6) Fark ve Durum hesapla
    merged["fark"] = merged["price_bizim"] - merged["price_rakip"]

    def fark_durum(f):
        if f < 0:
            return '🟢 Uygun'
        elif f > 0:
            return '🔴 Yüksek'
        return '🟡 Normal'

    merged["durum"] = merged["fark"].apply(fark_durum)

    # 7) Final tablo kolonları
    # Başlangıç, Bitiş, Bizim Konum, Rakip Konum,
    # Bizim İndirimli Fiyat, Rakip İndirimli Fiyat,
    # Aradaki Fark, Durum
    final_cols = [
        "pf_our",
        "pt_our",
        "loc_our",  # Bizim Konum
        "loc_comp",  # Rakip Konum
        "discounted_price_our",
        "discounted_price_rakip",
        "fark",
        "durum"
    ]
    final_df = merged[final_cols].copy()

    final_df.rename(columns={
        "pf_our": "Başlangıç",
        "pt_our": "Bitiş",
        "loc_our": "Bizim Konum",
        "loc_comp": "Rakip Konum",
        "discounted_price_our": "Bizim İndirimli Fiyat",
        "discounted_price_rakip": "Rakip İndirimli Fiyat",
        "fark": "Aradaki Fark",
        "durum": "Durum"
    }, inplace=True)

    # 8) "Aradaki Fark" sütununu "€XX.XX" biçiminde gösterelim
    # (İsterseniz "Bizim İndirimli Fiyat", "Rakip İndirimli Fiyat" vb. sütunları da benzer şekilde formatlayabilirsiniz.)
    final_df["Aradaki Fark"] = final_df["Aradaki Fark"].apply(lambda x: f"€{x:.2f}")

    # 9) Tabloyu göster
    st.dataframe(final_df, use_container_width=True)


def start_bot(platform_name):
    """Start the bot and check/update data"""
    try:
        response = requests.post(
            f"{API_URL}/api/v1/bot/start",
            headers={"Authorization": f"Bearer {st.session_state['token']}"}
        )
        if response.ok:
            data = response.json()
            st.success(data["message"])
            # Refresh the page after successful bot run
            if data.get("updated", False):
                st.rerun()
        else:
            st.error(f"Bot başlatma hatası: {response.text}")
    except Exception as e:
        st.error(f"Hata: {str(e)}")


def stop_bot(platform_name):
    """Stop the bot"""
    try:
        response = requests.post(
            f"{API_URL}/api/bot/stop",
            headers={"Authorization": f"Bearer {st.session_state['token']}"}
        )
        if response.ok:
            st.error(f"{platform_name} botu durduruldu!")
        else:
            st.error(f"Bot durdurma hatası: {response.text}")
    except Exception as e:
        st.error(f"Hata: {str(e)}")


def render_platform_page(platform_name):
    headers = {
        "Authorization": f"Bearer {st.session_state['token']}"
    }
    st.title(f"{platform_name} Fiyat Takip Sistemi")

    # Bot Kontrolü
    st.sidebar.header("Bot Kontrolü")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button(f"🟢 {platform_name}\nBaşlat", use_container_width=True):
            start_bot(platform_name)

    with col2:
        if st.button(f"🔴 {platform_name}\nDurdur", use_container_width=True):
            stop_bot(platform_name)

    # 6 sütunlu layout:
    col1, col2, col3, col4 = st.columns(4)

    # 1) Tarih Seçimi + on_change (otomatik fetch_sailamor_yachts)
    with col1:
        st.date_input(
            label="Tarih",
            value=st.session_state["selected_date"],
            key="selected_date",
            on_change=lambda: fetch_sailamor_yachts(str(platform_name).lower(),headers)
            # Tarih değişince direkt bu fonksiyon çağrılacak
        )
    # 2) Bizim Tekne Seçimi
    with col2:
        st.selectbox(
            "Bizim Tekne",
            options=["Seçiniz"] + st.session_state["our_yacht_list"],
            key="selected_yacht",
        )

    # 3) Rakip Firma Seçimi + on_change (fetch_competitor_yachts)
    with col3:
        st.selectbox(
            "Rakip Firma",
            options=["Seçiniz"] + st.session_state["competitor_list"],
            key="selected_competitor",
            on_change=lambda: fetch_competitor_yachts(str(platform_name).lower(),headers)
        )

    # 4) Rakip Tekne Seçimi (değiştiğinde belki başka işlem yapacaksanız on_change ekleyebilirsiniz)
    with col4:
        st.selectbox(
            "Rakip Tekne",
            options=["Seçiniz"] + st.session_state["competitor_yacht_list"],
            key="selected_competitor_yacht",
        )

    compare_prices(platform_name,headers)


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
        # 1) /login endpoint'ine POST isteği at
        login_data = {
            "username": email,
            "password": password
        }
        try:
            resp = requests.post(f"{API_BASE}/login", json=login_data)
            if resp.status_code == 200:
                # 2) Yanıtı parse et
                data = resp.json()  # { "access_token": "...", "token_type": "bearer" }
                token = data["access_token"]
                st.session_state["token"] = token
                st.session_state["is_logged_in"] = True
                st.experimental_rerun()
            else:
                # 401 veya başka hata
                st.error(f"Giriş başarısız: {resp.text}")
        except Exception as e:
            st.error(f"Sunucu hatası: {e}")

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
    if "selected_date" not in st.session_state:
        st.session_state["selected_date"] = date.today()
    if "our_yacht_list" not in st.session_state:
        st.session_state["our_yacht_list"] = []
    if "selected_yacht" not in st.session_state:
        st.session_state["selected_yacht"] = ""

    if "our_periods_raw" not in st.session_state:
        st.session_state["our_periods_raw"] = []
    if "selected_period_label" not in st.session_state:
        st.session_state["selected_period_label"] = "Seçiniz"

    if "competitor_list" not in st.session_state:
        st.session_state["competitor_list"] = ["Rudder&Moor", "Sailtime", "NaviGo"]  # sabit
    if "selected_competitor" not in st.session_state:
        st.session_state["selected_competitor"] = "Seçiniz"

    if "competitor_yacht_list" not in st.session_state:
        st.session_state["competitor_yacht_list"] = []
    if "selected_competitor_yacht" not in st.session_state:
        st.session_state["selected_competitor_yacht"] = "Seçiniz"


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
