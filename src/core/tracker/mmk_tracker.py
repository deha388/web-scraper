import re
import json
import logging
import time
import datetime
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import asyncio

from src.infra.config.config import COMPETITORS_MMK as COMPETITORS
from src.infra.config.settings import MMK_USERNAME, MMK_PASSWORD
from src.infra.config.init_database import init_database
from src.infra.adapter.booking_data_repository import BookingDataRepository
from src.infra.adapter.update_log_repository import UpdateLogRepository


class MMKTracker:
    def __init__(self):
        self.driver = None
        self.logger = logging.getLogger(self.__class__.__name__)
        # Login URL sabit
        self.login_url = "https://portal.booking-manager.com/wbm2/app/login_register/"
        self.logged_in = False

    @staticmethod
    def format_currency(value):

        try:
            s = "{:,.2f}".format(value)
        except Exception:
            s = "0.00"
        s = s.replace(",", "X").replace(".", ",").replace("X", ".")
        return s

    def setup_driver(self):
        """Driver kurulumu"""
        self.logger.info("Driver kurulumu başlıyor...")
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.binary_location = '/usr/bin/chromium'
        service = Service('/usr/bin/chromedriver')
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)
        self.logger.info("Driver başarıyla kuruldu.")

    def wait_and_find_element(self, by, value, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def wait_for_clickable(self, by, value, timeout=10):
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )

    def safe_click(self, element):
        try:
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(element))
            element.click()
            return True
        except Exception as e:
            self.logger.error(f"Tıklama hatası: {str(e)}")
            return False

    async def login(self):
        """Selenium ile giriş yapar ve cookie'leri hazırlar."""
        if self.logged_in:
            self.logger.info("Zaten login durumundasınız, tekrar giriş yapılmadı.")
            return True
        try:
            self.driver.get(self.login_url)
            time.sleep(5)
            username = self.wait_and_find_element(By.NAME, "login_email")
            password = self.wait_and_find_element(By.NAME, "login_password")
            username.send_keys(MMK_USERNAME)
            password.send_keys(MMK_PASSWORD)
            login_button = self.wait_for_clickable(By.CSS_SELECTOR, "input[type='submit'][value='Login']")
            self.safe_click(login_button)
            WebDriverWait(self.driver, 10).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CLASS_NAME, "main-container")),
                    EC.presence_of_element_located((By.CLASS_NAME, "navbar-container"))
                )
            )
            self.logger.info("MMK Booking Manager'a başarıyla giriş yapıldı")
            self.logged_in = True
            await asyncio.sleep(5)
            return True
        except Exception as e:
            self.logger.error(f"MMK login hatası: {str(e)}")
            self.logger.error(f"Hata detayı: {type(e).__name__}")
            return False

    def get_session(self):
        """Selenium driver'dan cookie'leri alıp requests Session'ına ekler."""
        cookies = self.driver.get_cookies()
        session = requests.Session()
        for cookie in cookies:
            session.cookies.set(cookie['name'], cookie['value'])
        return session

    async def fetch_competitor_weekly_price_quotes(self, book_repo, update_log_repo):

        session = self.get_session()
        today = datetime.date.today()
        days_ahead = 5 - today.weekday()
        if days_ahead < 0:
            days_ahead += 7
        next_saturday = today + datetime.timedelta(days=days_ahead)
        period_end = next_saturday + datetime.timedelta(days=180)  # Örneğin 6 ay
        base_url = "https://portal.booking-manager.com/wbm2/page.html"
        results = []

        for competitor_name, comp_data in COMPETITORS.items():
            self.logger.info(f"Rakip: {competitor_name} için işlemler başlatılıyor...")
            json_response = session.get(comp_data["url"], params=comp_data["params"])
            try:
                data = json_response.json()
            except Exception as e:
                self.logger.error(f"{competitor_name} için JSON verisi alınamadı: {str(e)}")
                continue

            if "boats" not in data:
                self.logger.warning(f"{competitor_name} için 'boats' verisi bulunamadı.")
                continue

            boats = data["boats"]
            for yacht_name, yacht_id in comp_data["yacht_ids"].items():
                existing_booking = await book_repo.get_daily_booking_data(competitor_name, yacht_id, datetime.date.today())
                if existing_booking:
                    self.logger.info(f"Güncel veri mevcut: {competitor_name} - {yacht_name}. Güncelleme atlanıyor.")
                    continue
                self.logger.info(
                    f"Rakip: {competitor_name} - Yat: {yacht_name} (ID: {yacht_id}) için haftalık işlemler başlatılıyor...")
                boat_data = next((b for b in boats if b.get("id") == yacht_id), None)
                if boat_data:
                    resource_id = boat_data["id"]
                    base_id = boat_data.get("baseId", "")
                    product_id = boat_data.get("product", [{}])[0].get("id", "Bareboat")
                    yacht_fullname = boat_data.get("fullName", yacht_name)
                    company_name = boat_data.get("company", competitor_name)
                    if "Turizm" in company_name:
                        company_name = company_name.replace(" Turizm", "")
                    port = boat_data.get("base", "")
                    deposit_val = boat_data.get("deposit", 0)
                else:
                    resource_id = yacht_id
                    base_id = comp_data.get("baseId", "")
                    product_id = comp_data.get("product", "Bareboat")
                    yacht_fullname = yacht_name
                    company_name = competitor_name
                    port = ""
                    deposit_val = 0

                booking_periods = []
                current_start = next_saturday
                while current_start < period_end:
                    current_end = current_start + datetime.timedelta(days=7)
                    dt_from = datetime.datetime(current_start.year, current_start.month, current_start.day, 0, 0)
                    dt_to = datetime.datetime(current_end.year, current_end.month, current_end.day, 0, 0)
                    dateFrom_ms = int(time.mktime(dt_from.timetuple()) * 1000)
                    dateTo_ms = int(time.mktime(dt_to.timetuple()) * 1000)

                    params_add = {
                        'view': 'PriceQuoteQueueBETA',
                        'action': 'addToQueue',
                        'resourceid': resource_id,
                        'dateFrom': dateFrom_ms,
                        'dateTo': dateTo_ms,
                        'reservationId': '',
                        'baseFromId': base_id,
                        'baseToId': base_id,
                        'product': product_id,
                        'extraDiscount': '0.0'
                    }
                    response_add = session.post(base_url, params=params_add)
                    if response_add.status_code != 200:
                        self.logger.warning(
                            f"{competitor_name} - {yacht_name} için addToQueue başarısız! Tarih: {current_start} - {current_end}")
                        current_start = current_end
                        continue

                    response_add.encoding = 'utf-8'
                    soup = BeautifulSoup(response_add.text, "html.parser")
                    price_text = None
                    price_labels = soup.find_all("div", string=lambda s: s and "Price:" in s)
                    for label in price_labels:
                        sibling = label.find_next_sibling("div")
                        if sibling:
                            text = sibling.get_text(strip=True)
                            if re.search(r'^\d', text) and "NaN" not in text:
                                price_text = text
                                break

                    if not price_text:
                        self.logger.warning(
                            f"{competitor_name} - {yacht_name} için Price bilgisi alınamadı. Tarih: {current_start} - {current_end}")
                        current_start = current_end
                        continue

                    if "(" in price_text:
                        price_pattern = r'([\d,\.]+)\s*€\s*\(\s*([\d,\.]+)\s*€\s*-\s*([\d,\.]+)%\)'
                        m = re.search(price_pattern, price_text)
                        if m:
                            total_price_str = m.group(1)
                            list_price_str = m.group(2)
                            discount_percent_str = m.group(3) + "%"
                            try:
                                total_price_val = float(total_price_str.replace(",", ""))
                                list_price_val = float(list_price_str.replace(",", ""))
                            except Exception as e:
                                self.logger.error(f"Fiyat dönüşüm hatası: {e}")
                                current_start = current_end
                                continue
                            discount_amount_val = list_price_val - total_price_val
                        else:
                            self.logger.warning(
                                f"{competitor_name} - {yacht_name} için Price metni parse edilemedi: {price_text}")
                            current_start = current_end
                            continue
                    else:
                        price_clean = price_text.replace("€", "").strip()
                        try:
                            total_price_val = float(price_clean.replace(",", ""))
                        except Exception as e:
                            self.logger.error(f"Fiyat dönüşüm hatası: {e}")
                            current_start = current_end
                            continue
                        list_price_val = total_price_val
                        discount_percent_str = "0%"
                        discount_amount_val = 0.0

                    commission_div = soup.find("div", string=lambda s: s and "Commission" in s)
                    commission_percentage = None
                    commission_amount_val = None
                    if commission_div:
                        commission_div_text = commission_div.get_text(strip=True)
                        match_comm = re.search(r"Commission\s+([\d,\.]+%)", commission_div_text)
                        if match_comm:
                            commission_percentage = match_comm.group(1)
                        sibling_div = commission_div.find_next_sibling("div")
                        if sibling_div:
                            inp = sibling_div.find("input", {"type": "number"})
                            if inp and inp.has_attr("value"):
                                try:
                                    commission_amount_val = float(inp["value"].replace(",", ""))
                                except Exception as e:
                                    self.logger.error(f"Commission dönüşüm hatası: {e}")
                    else:
                        self.logger.warning(f"{competitor_name} - {yacht_name} için Commission bilgisi bulunamadı.")

                    total_div = soup.find("div", string=lambda s: s and "Total:" in s)
                    total_text = None
                    if total_div:
                        sibling_div = total_div.find_next_sibling("div")
                        if sibling_div:
                            inp = sibling_div.find("input", {"type": "number"})
                            if inp and inp.has_attr("value"):
                                total_text = inp["value"]
                    if not total_text:
                        total_text = str(total_price_val)

                    client_price_val = total_price_val
                    agency_price_val = client_price_val - (commission_amount_val if commission_amount_val else 0)
                    formatted_list_price = self.format_currency(list_price_val)
                    formatted_total_price = self.format_currency(total_price_val)
                    formatted_discount = "-" + self.format_currency(discount_amount_val)
                    formatted_deposit = self.format_currency(deposit_val)
                    formatted_commission = self.format_currency(
                        commission_amount_val) if commission_amount_val is not None else ""
                    formatted_client_price = self.format_currency(client_price_val)
                    formatted_agency_price = self.format_currency(agency_price_val)
                    period_from_str = dt_from.strftime("%Y-%m-%d %H:%M:%S")
                    period_to_str = dt_to.strftime("%Y-%m-%d %H:%M:%S")
                    discount_name = "Discount"

                    period_detail = {
                        "period_from": period_from_str,
                        "period_to": period_to_str,
                        "details": [
                            {
                                "discount_name": discount_name,
                                "yacht_name": yacht_fullname,
                                "company_name": company_name,
                                "port_from": port,
                                "port_to": port,
                                "deposit": formatted_deposit,
                                "discount_percent": discount_percent_str,
                                "list_price": formatted_list_price,
                                "discount": formatted_discount,
                                "total_price": formatted_total_price,
                                "commission_percent": commission_percentage,
                                "commission": formatted_commission,
                                "client_price": formatted_client_price,
                                "agency_price": formatted_agency_price,
                                "agency_income": formatted_commission,
                                "total_advanced_payment": formatted_client_price
                            }
                        ]
                    }
                    booking_periods.append(period_detail)
                    self.logger.info(
                        f"[{competitor_name} - {yacht_name}] Tarih: {period_from_str} - {period_to_str} | "
                        f"Price={formatted_total_price} € (List: {formatted_list_price} € - {discount_percent_str}) | "
                        f"Commission Oran={commission_percentage} | Commission Tutar={formatted_commission}"
                    )
                    params_clear = {'view': 'PriceQuoteQueueBETA', 'action': 'clearQueue'}
                    session.post(base_url, params=params_clear)
                    await asyncio.sleep(15)
                    current_start = current_end

                record = {
                    "yacht_id": resource_id,
                    "booking_periods": booking_periods,
                    "competitor": competitor_name
                }
                results.append(record)
                today_dt = datetime.datetime.now()
                await book_repo.save_daily_booking_data(competitor_name, [record])
                await update_log_repo.create_one(update_log_repo.collection_name, {
                    "competitor": competitor_name,
                    "yacht_id": resource_id,
                    "last_update_date": today_dt,
                    "status": "success",
                    "timestamp": datetime.datetime.now()
                })
                await asyncio.sleep(30)

            await asyncio.sleep(60)

        print(json.dumps({"results": results}, indent=4, ensure_ascii=False, default=str))
        return results

    def cleanup(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.logged_in = False


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    tracker = MMKTracker()
    tracker.setup_driver()
    db_conf = init_database()
    db_client = db_conf.db_session
    database = db_client["boat_tracker"]
    book_repo = BookingDataRepository(database, "booking_data_mmk")
    update_log_repo = UpdateLogRepository(database)

    if asyncio.run(tracker.login()):
        asyncio.run(tracker.fetch_competitor_weekly_price_quotes(book_repo=book_repo, update_log_repo=update_log_repo))
    else:
        print("Giriş yapılamadı.")
    tracker.cleanup()
