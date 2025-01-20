# src/core/tracker/nausys_tracker.py

import asyncio
import time
import logging
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
    - scrape_yacht_ids_and_save:
        Rakip ismi + search_text + click_text -> Nausys'te firma filtreler, ID'leri okur.
        DB'ye competitor kaydı (yacht_ids, search_text, click_text).
    - collect_data_and_save:
        DB'de bugüne ait verisi eksik olan rakipleri bulur,
        her biri için sayfada filtre uygular -> fetch_booking_details -> kaydeder.
    """

    def __init__(self):
        super().__init__()
        self.base_url = "https://agency.nausys.com"
        self.driver = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logged_in = False
        self.db_conf = init_database()

    # ------------------------------------------------------------------------------
    # Selenium Setup / Login
    # ------------------------------------------------------------------------------
    def setup_driver(self):
        self.logger.info("Driver kurulumu başlıyor...")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service)
        self.driver.maximize_window()
        self.logger.info("Driver başarıyla kuruldu ve pencere maximize edildi.")

    def login(self):
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

            # Gerçek kullanıcı / şifre
            username.send_keys("user@SAAMO")
            password.send_keys("sail1234")

            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
            )
            login_button.click()

            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".layout-main"))
            )
            self.logger.info("Nausys'e başarıyla giriş yapıldı.")
            self.logged_in = True
            return True
        except Exception as e:
            self.logger.error(f"Nausys login hatası: {str(e)}")
            return False

    def go_to_booking_list_page(self):
        try:
            if not self.logged_in:
                self.logger.info("Login durumu FALSE, otomatik login deniyor...")
                if not self.login():
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
            raise

    # ------------------------------------------------------------------------------
    # 1) Scraping Metotları
    # ------------------------------------------------------------------------------
    def select_autocomplete_item(self, input_css, panel_css, text_to_type, text_to_click):
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
            desired_li = None
            for li in all_li:
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
            raise

    def select_charter_company_and_search(self, company_search_text, company_click_text):
        try:
            self.logger.info(f"Charter company '{company_search_text}' seçiliyor...")
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
            self.logger.info(f"'{company_search_text}' için arama işlemi tamamlandı.")
        except Exception as e:
            self.logger.error(f"Charter firma seçerken hata: {str(e)}")
            raise

    def get_yacht_ids_from_page(self) -> list:
        try:
            yacht_ids = []
            yacht_rows = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "YachtRow"))
            )
            self.logger.info(f"Toplam {len(yacht_rows)} adet 'YachtRow' bulundu.")

            for row in yacht_rows:
                try:
                    row_body = row.find_element(By.CSS_SELECTOR, "[id^='y-']")
                    row_id = row_body.get_attribute('id')
                    yacht_id_match = re.search(r'y-(\d+)-', row_id)
                    if yacht_id_match:
                        yacht_ids.append(yacht_id_match.group(1))
                except Exception as row_error:
                    self.logger.error(f"YachtRow işleme hatası: {str(row_error)}")
                    continue
            self.logger.info(f"Toplam {len(yacht_ids)} adet YACHT ID bulundu: {yacht_ids}")
            return yacht_ids
        except Exception as e:
            self.logger.error(f"Yacht ID'leri alınırken hata: {str(e)}")
            return []

    async def scrape_yacht_ids_and_save(
        self,
        competitor_name: str,
        company_search_text: str,
        company_click_text: str
    ):
        """
        1) Selenium login + bookingList
        2) Firma filtre (company_search_text, company_click_text)
        3) Yat ID'lerini çek
        4) DB'ye upsert_competitor_info (competitor_name, yacht_ids, search_text, click_text)
        """

        self.logger.info(f"Scrape süreci başlatıldı: '{company_search_text}' / '{company_click_text}'")
        if not self.logged_in:
            if not self.login():
                self.logger.error("Login başarısız, yat ID'leri çekilemedi.")
                return []

        self.go_to_booking_list_page()
        self.select_charter_company_and_search(company_search_text, company_click_text)
        time.sleep(2)

        yacht_ids = self.get_yacht_ids_from_page()
        db_client = self.db_conf.db_session
        database = db_client["boat_tracker"]
        nausys_repo = NausysRepository(database)

        # Rakip bilgileri + Search/Click text upsert
        await nausys_repo.upsert_competitor_info(
            competitor_name=competitor_name,
            yacht_ids=yacht_ids,
            search_text=company_search_text,
            click_text=company_click_text
        )

        self.logger.info(f"[{competitor_name}] Çekilen YACHT ID'leri DB'ye kaydedildi: {yacht_ids}")
        return yacht_ids

    # ------------------------------------------------------------------------------
    # 2) Booking Data Çekme (Requests)
    # ------------------------------------------------------------------------------
    def get_session_data(self):
        try:
            cookies = self.driver.get_cookies()
            jsessionid = next((c['value'] for c in cookies if c['name'] == 'JSESSIONID'), None)
            view_state = self.driver.execute_script("""
                return document.querySelector('input[name="javax.faces.ViewState"]').value;
            """)
            return jsessionid, view_state
        except Exception as e:
            self.logger.error(f"Session data alma hatası: {str(e)}")
            return None, None

    def fetch_booking_details(self, yacht_id, period_from, period_to):
        """
        Partial AJAX isteği ile (yacht_id, period_from, period_to) booking data.
        """
        try:
            jsessionid, view_state = self.get_session_data()
            if not jsessionid or not view_state:
                self.logger.error("Session bilgileri alınamadı!")
                return None

            url = "https://agency.nausys.com/NauSYS-agency/app/bookinglist.xhtml"
            headers = {
                "Accept": "application/xml, text/xml, */*; q=0.01",
                "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Faces-Request": "partial/ajax",
                "X-Requested-With": "XMLHttpRequest",
                "User-Agent": "Mozilla/5.0",
                "Referer": url
            }
            cookies = {"JSESSIONID": jsessionid}
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

            resp = requests.post(url, headers=headers, cookies=cookies, data=data)
            if not resp.ok:
                self.logger.error(f"API isteği başarısız: {resp.status_code}")
                return None

            soup = BeautifulSoup(resp.text, "xml")
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
                            params = [p.strip().strip("'") for p in
                                      params_str.group(1).split(',')] if params_str else []

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
        except Exception as e:
            self.logger.error(f"Booking detayları çekerken hata: {str(e)}")
            return None

    @staticmethod
    def generate_weekly_dates(start_date_str="2025-04-12", end_date_str="2025-10-25"):
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

    # ------------------------------------------------------------------------------
    # 3) Data Toplama (Eksik Rakipler)
    # ------------------------------------------------------------------------------
    async def collect_data_and_save(self):
        """
        1) DB'den bugüne dair verisi olmayan rakipleri al (get_competitors_missing_data_for_today)
        2) Her rakip için:
             -> go_to_booking_list_page
             -> select_charter_company_and_search (search_text, click_text)
             -> fetch_booking_details
             -> DB'ye kaydet
        """
        if not self.logged_in:
            if not self.login():
                self.logger.error("Login başarısız oldu, data toplanamıyor.")
                return

        db_client = self.db_conf.db_session
        database = db_client["boat_tracker"]
        nausys_repo = NausysRepository(database)

        missing_competitors = await nausys_repo.get_competitors_missing_data_for_today()
        if not missing_competitors:
            self.logger.info("Hiçbir rakip için bugünün verisi eksik değil. İşlem yapılmıyor.")
            return

        date_ranges = self.generate_weekly_dates()
        self.logger.info(f"Toplam {len(date_ranges)} haftalık periyot üretildi.")

        for competitor_name, yacht_ids in missing_competitors.items():
            self.logger.info(f"\nFirma: {competitor_name}, Yat IDs: {yacht_ids}")

            competitor_doc = await nausys_repo.get_competitor_doc(competitor_name)
            if not competitor_doc:
                self.logger.warning(f"{competitor_name} dokümanı bulunamadı, atlanıyor.")
                continue

            search_text = competitor_doc.get("search_text", "")
            click_text = competitor_doc.get("click_text", "")

            if not search_text or not click_text:
                self.logger.warning(f"{competitor_name} için search_text/click_text eksik. Atlanıyor.")
                continue

            # Sayfaya gidip rakip filtre uygula
            self.go_to_booking_list_page()
            self.select_charter_company_and_search(search_text, click_text)
            time.sleep(2)

            # Her Yat ID için, date_ranges'ta fetch -> save
            for yid in yacht_ids:
                self.logger.info(f"-- Yat ID: {yid}")
                for (p_from, p_to) in date_ranges:
                    details = self.fetch_booking_details(yid, p_from, p_to)
                    if details:
                        data_to_insert = {
                            "yacht_id": yid,
                            "booking_periods": [
                                {
                                    "period_from": p_from,
                                    "period_to": p_to,
                                    "details": details
                                }
                            ]
                        }
                        await nausys_repo.save_booking_data(competitor_name, [data_to_insert])
                        self.logger.info(f"  * {p_from} -> {p_to} için {len(details)} kayıt kaydedildi.")
                    else:
                        self.logger.warning(f"  - {p_from} -> {p_to} için veri bulunamadı.")

        self.logger.info("Tüm eksik rakipler için data toplama işlemi tamamlandı.")


# ---------------------------
# Test
# ---------------------------
async def test_nausys_bot():
    logging.basicConfig(level=logging.INFO)
    bot = NausysTracker()
    bot.setup_driver()
    try:
        # competitor = "sailamor"
        # search = "Sailamor"
        # click = "Sailamor"
        # yacht_ids = await bot.scrape_yacht_ids_and_save(competitor, search, click)
        # logging.info(f"\nScrape sonucu Yat ID'leri (kaydedilenler): {yacht_ids}")

        await bot.collect_data_and_save()
        logging.info("Tüm işlem tamamlandı.")
    except Exception as e:
        logging.error(f"Test sırasında hata oluştu: {str(e)}")
    finally:
        time.sleep(3)
        if bot.driver:
            bot.driver.quit()

if __name__ == "__main__":
    asyncio.run(test_nausys_bot())
