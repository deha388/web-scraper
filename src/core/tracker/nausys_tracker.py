import asyncio
import time
import logging
import json
import requests
import re

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from src.infra.config.init_database import init_database
from src.infra.adapter.nausys_repository import NausysRepository


class BaseTracker:
    def setup_driver(self):
        pass


class NausysTracker(BaseTracker):
    """
    Nausys üzerinden yat ID’lerini çekmek ve rezervasyon verilerini incelemek için
    Selenium + Requests kullanan bir tracker sınıfı.
    """

    YACHT_IDS = {
        "rudder_moor": [
            "34432275", "34431785", "51917352", "40241064", "34431144",
            "51132504", "34669520", "40241119", "34669521", "34431219",
            "34431269", "40241056", "40239533", "40241379", "40241357",
            "34431195", "34431197", "40241092", "34431207", "34431211",
            "34669522", "34431226", "34431194", "34431198"
        ]
    }

    def __init__(self):
        super().__init__()
        self.base_url = "https://agency.nausys.com"
        self.driver = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logged_in = False

        self.db_conf = init_database()

    def setup_driver(self):
        """Chrome driver'ı kurar ve başlatır."""
        self.logger.info("Driver kurulumu başlıyor...")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)
        self.driver.maximize_window()
        self.logger.info("Driver başarıyla kuruldu ve pencere maximize edildi.")

    def login(self):
        """Selenium ile Nausys'e giriş yapar."""
        if self.logged_in:
            self.logger.info("Zaten login durumundasınız, tekrar giriş yapılmadı.")
            return True
        try:
            self.logger.info("Nausys ana sayfası açılıyor...")
            self.driver.get(self.base_url)
            self.logger.info("Login form elementleri bekleniyor...")
            username = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            password = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            self.logger.info("Kullanıcı bilgileri giriliyor...")
            username.clear()
            password.clear()
            username.send_keys("user@SAAMO")  # Kendi kullanıcı adınız
            password.send_keys("sail1234")    # Kendi şifreniz
            self.logger.info("Login butonuna tıklanıyor...")
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
            )
            login_button.click()
            self.logger.info("Ana sayfa yüklenmesi bekleniyor...")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".layout-main"))
            )
            self.logger.info("Nausys'e başarıyla giriş yapıldı.")
            self.logged_in = True
            return True
        except Exception as e:
            self.logger.error(f"Nausys login hatası: {str(e)}")
            self.logger.error(f"Hata detayı: {type(e).__name__}")
            self.logger.error(f"Sayfa kaynağı: {self.driver.page_source}")
            return False

    def select_autocomplete_item(self, input_css, panel_css, text_to_type, text_to_click):
        """
        Autocomplete input'a text yazıp panelde beliren seçeneklerden
        text_to_click geçen elemana tıklar.
        """
        try:
            input_box = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, input_css))
            )
            input_box.clear()
            input_box.send_keys(text_to_type)
            time.sleep(1)

            panel = WebDriverWait(self.driver, 15).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, panel_css))
            )
            all_li = panel.find_elements(By.TAG_NAME, "li")
            self.logger.info(f"Paneldeki li sayısı: {len(all_li)}")

            desired_li = None
            for li in all_li:
                # text_to_click'i lower() ile kıyaslayabilirsiniz
                if text_to_click.lower() in li.text.lower():
                    desired_li = li
                    break

            if desired_li:
                WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable(desired_li)
                )
                desired_li.click()
                self.logger.info(f"Autocomplete: '{text_to_type}' yazıldı, '{text_to_click}' seçildi.")
            else:
                self.logger.warning(f"Panelde '{text_to_click}' metnine sahip li bulunamadı.")
        except Exception as e:
            self.logger.error(f"Autocomplete item seçerken hata: {str(e)}")
            self.logger.error(f"Panel kaynağı: {self.driver.page_source}")
            raise

    def go_to_booking_list_page(self):
        """
        Ana booking list sayfasına gider. Eğer login değilse, otomatik login olmaya çalışır.
        """
        try:
            if not self.logged_in:
                self.logger.info("Login durumu FALSE, otomatik login deniyor...")
                login_success = self.login()
                if not login_success:
                    self.logger.error("Login başarısız oldu, booking list sayfasına gidilemiyor.")
                    return
            self.logger.info("Booking list sayfasına yönlendiriliyor...")
            self.driver.get("https://agency.nausys.com/NauSYS-agency/app/bookinglist.xhtml")
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".layout-main"))
            )
            self.logger.info("Booking list sayfası başarıyla yüklendi.")
        except Exception as e:
            self.logger.error(f"Booking list sayfasına giderken hata oluştu: {str(e)}")
            self.logger.error(f"Sayfa kaynağı: {self.driver.page_source}")
            raise

    def select_charter_company_and_search(self, company_search_text, company_click_text):
        """
        Parametrik bir şekilde charter firması seçip 'Search' butonuna tıklar.
        :param company_search_text: Autocomplete'e yazılacak metin (örn. "Rudder & Moor")
        :param company_click_text: Autocomplete listesinde tıklanacak kısım (örn. "rudder&moor")
        """
        try:
            self.logger.info("Charter company seçiliyor...")
            self.select_autocomplete_item(
                input_css="input[id$='charterCompanyAutocompleteComponentId2_input']",
                panel_css="span[id$='charterCompanyAutocompleteComponentId2_panel']",
                text_to_type=company_search_text,
                text_to_click=company_click_text
            )
            time.sleep(1)
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id$='searchBtn']"))
            )
            search_button.click()
            time.sleep(5)
            self.logger.info(f"'{company_search_text}' için arama tamamlandı.")
        except Exception as e:
            self.logger.error(f"Hata: {str(e)}")
            raise

    def get_yacht_ids(self):
        """
        Booking list sayfasındaki 'YachtRow' elemanlarından id bilgilerini alır.
        """
        try:
            yacht_ids = []
            yacht_rows = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "YachtRow"))
            )
            self.logger.info(f"Toplam {len(yacht_rows)} yacht row bulundu.")

            for yacht_row in yacht_rows:
                try:
                    row_body = yacht_row.find_element(By.CSS_SELECTOR, "[id^='y-']")
                    row_id = row_body.get_attribute('id')
                    yacht_id_match = re.search(r'y-(\d+)-', row_id)
                    if yacht_id_match:
                        yacht_id = yacht_id_match.group(1)
                        yacht_ids.append(yacht_id)
                        self.logger.info(f"Yacht ID bulundu: {yacht_id}")
                except Exception as row_error:
                    self.logger.error(f"Row işleme hatası: {str(row_error)}")
                    continue

            self.logger.info(f"Toplam {len(yacht_ids)} yacht ID'si bulundu: {yacht_ids}")
            return yacht_ids
        except Exception as e:
            self.logger.error(f"Yacht ID'leri alınırken hata: {str(e)}")
            return []

    def get_session_data(self):
        """
        Selenium üzerinden aktif oturumun cookie (JSESSIONID) ve viewState değerlerini alır.
        """
        try:
            cookies = self.driver.get_cookies()
            jsessionid = next((cookie['value'] for cookie in cookies if cookie['name'] == 'JSESSIONID'), None)
            view_state = self.driver.execute_script("""
                return document.querySelector('input[name="javax.faces.ViewState"]').value;
            """)
            return jsessionid, view_state
        except Exception as e:
            self.logger.error(f"Session data alma hatası: {str(e)}")
            return None, None

    def fetch_booking_details(self, yacht_id, period_from, period_to):
        """
        Tek bir yat ID ve tarih aralığı için partial/ajax isteği atarak booking detaylarını çeker.
        Dönecek veri, "status", "prices", "discount" vb. bilgileri içerir.
        """
        try:
            jsessionid, view_state = self.get_session_data()
            if not jsessionid or not view_state:
                self.logger.error("Session bilgileri alınamadı")
                return None

            url = "https://agency.nausys.com/NauSYS-agency/app/bookinglist.xhtml"
            headers = {
                "Accept": "application/xml, text/xml, */*; q=0.01",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Faces-Request": "partial/ajax",
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
                "Referer": url
            }
            cookies = {
                "JSESSIONID": jsessionid
            }
            data = {
                "javax.faces.partial.ajax": "true",
                "javax.faces.source": "searchResultsForm:dailyBookingListComponent",
                "javax.faces.partial.execute": "searchResultsForm:dailyBookingListComponent",
                "javax.faces.partial.render": "searchResultsForm:dailyBookingListComponent",
                "searchResultsForm:dailyBookingListComponent": "searchResultsForm:dailyBookingListComponent",
                "action": "fetchBookingDiv",
                "yachtId": yacht_id,
                "periodFrom": period_from,
                "periodTo": period_to,
                "locationId": "",
                "reservationType": "free",
                "menuform": "menuform",
                "javax.faces.ViewState": view_state
            }

            response = requests.post(url, headers=headers, cookies=cookies, data=data)
            if response.ok:
                soup = BeautifulSoup(response.text, "xml")
                updates = soup.find_all("update")
                booking_data = []
                for upd in updates:
                    if upd.get("id") == "searchResultsForm:dailyBookingListComponent":
                        cdata_content = upd.string
                        if cdata_content:
                            inner_soup = BeautifulSoup(cdata_content, "html.parser")
                            daily_res_items = inner_soup.find_all("div", class_="dailyRes")
                            for item in daily_res_items:
                                basket_cart = item.find("div", class_="addToBasketCart")
                                onclick_attr = basket_cart.get("onclick", "") if basket_cart else ""
                                params_str = re.search(r'\((.*?)\)', onclick_attr)
                                params = [p.strip().strip("'") for p in params_str.group(1).split(',')] if params_str else []
                                status_div = item.find("div", class_="dailyRes-status")
                                status = status_div.get_text(strip=True) if status_div else "N/A"

                                bases_div = item.find("div", class_="dailyRes-bases")
                                location = bases_div.get_text(strip=True) if bases_div else "N/A"

                                price_div = item.find("div", class_="dailyRes-price")
                                discounted_price = "N/A"
                                original_price = "N/A"
                                discount_percentage = None

                                if price_div:
                                    big_price = price_div.find("span", class_="dailyBigPrice")
                                    small_price = price_div.find("span", class_="dailySmallPrice")
                                    if big_price:
                                        discounted_price = big_price.get_text(strip=True)
                                    if small_price:
                                        small_price_text = small_price.get_text(strip=True)
                                        original_price_match = re.search(r'\(([\d.,]+)', small_price_text)
                                        if original_price_match:
                                            original_price = f"{original_price_match.group(1)} EUR"
                                        discount_match = re.search(r'-> (\d+) %', small_price_text)
                                        if discount_match:
                                            discount_percentage = f"{discount_match.group(1)}%"

                                booking_info = {
                                    "yacht_name": params[1] if len(params) > 1 else "N/A",
                                    "status": status,
                                    "location": location,
                                    "prices": {
                                        "discounted_price": discounted_price,
                                        "original_price": original_price,
                                        "discount_percentage": discount_percentage
                                    }
                                }
                                booking_data.append(booking_info)
                return booking_data
            else:
                self.logger.error(f"API isteği başarısız: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Booking detayları çekerken hata: {str(e)}")
            return None

    def generate_weekly_dates(self, start_date_str="2025-04-12", end_date_str="2025-10-25"):
        """
        Cumartesiden cumartesiye (örnek) haftalık tarih aralıklarını üretir.
        period_from = yyyy-mm-dd 17:00:00
        period_to   = yyyy-mm-dd 08:00:00
        """
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        date_pairs = []
        current_date = start_date
        while current_date < end_date:
            period_from = f"{current_date.strftime('%Y-%m-%d')} 17:00:00"
            period_to = f"{(current_date + timedelta(days=7)).strftime('%Y-%m-%d')} 08:00:00"
            date_pairs.append((period_from, period_to))
            current_date += timedelta(days=7)
        return date_pairs

    async def process_all_yachts(
        self,
        company_search_text="Sailamor",
        company_click_text="Sailamor",
        yacht_ids_dict=None
    ):
        """
        Hem scraping (Selenium) hem de Request akışını yapan genel örnek metot.
        1) Gerekliyse login olup BookingList sayfasına gider.
        2) Belirtilen Charter Company seçilip Search yapılır.
        3) YACHT ID’leri sayfadan çekilir (ya da dışarıdan gelen dictionary de kullanılabilir).
        4) Tarih aralıklarında API isteği atıp booking verileri çekilir ve DB'ye kaydedilir.
        """

        if yacht_ids_dict is None:
            yacht_ids_dict = self.YACHT_IDS

        db_client = self.db_conf.db_session
        database = db_client["boat_tracker"]
        nausys_repo = NausysRepository(database)

        if not self.logged_in:
            success = self.login()
            if not success:
                self.logger.error("Login başarısız!")
                return

        self.go_to_booking_list_page()
        self.select_charter_company_and_search(company_search_text, company_click_text)
        time.sleep(5)
        scraped_ids = self.get_yacht_ids()
        date_pairs = self.generate_weekly_dates()
        company_results = {}

        company_key = "sailamor"
        company_results[company_key] = {}
        combined_ids = set(scraped_ids)
        combined_ids.update(yacht_ids_dict.get("sailamor", []))

        for yacht_id in combined_ids:
            self.logger.info(f"\nYat ID {yacht_id} için işlemler başlıyor...")
            company_results[company_key][yacht_id] = []
            for period_from, period_to in date_pairs:
                try:
                    self.logger.info(f"Tarih aralığı: {period_from} - {period_to}")
                    booking_details = self.fetch_booking_details(yacht_id, period_from, period_to)
                    if booking_details:
                        period_result = {
                            "period_from": period_from,
                            "period_to": period_to,
                            "details": booking_details
                        }

                        single_insert_data = {
                            "yacht_id": yacht_id,
                            "booking_periods": [period_result]
                        }

                        await nausys_repo.save_booking_data(company_key, [single_insert_data])

                        time.sleep(1)
                        company_results[company_key][yacht_id].append(period_result)
                        self.logger.info("Booking detayları başarıyla kaydedildi.")
                    else:
                        self.logger.warning(f"Yacht ID {yacht_id} için {period_from} - {period_to} aralığında veri alınamadı.")
                    time.sleep(1)
                except Exception as e:
                    self.logger.error(f"Hata oluştu: {str(e)}")
                    continue

        self.logger.info("Tüm işlemler tamamlandı.")
        # Dilerseniz company_results'ı return edebilirsiniz
        return company_results


async def test_nausys_bot():
    logging.basicConfig(level=logging.INFO)
    try:
        bot = NausysTracker()
        bot.setup_driver()

        await bot.process_all_yachts(
            company_search_text="Sailamor",
            company_click_text="Sailamor"
        )
        logging.info("İşlemler tamamlandı.")
    except Exception as e:
        logging.error(f"Test sırasında hata oluştu: {str(e)}")
        raise
    finally:
        time.sleep(5)
        if 'bot' in locals() and hasattr(bot, 'driver'):
            bot.driver.quit()


if __name__ == "__main__":
    asyncio.run(test_nausys_bot())
