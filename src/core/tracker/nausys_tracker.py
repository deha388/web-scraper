import asyncio
import time
import logging
import requests
import re
from lxml import html
from datetime import datetime, timedelta, date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from src.infra.config.config import COMPETITORS
from src.infra.config.init_database import init_database
from src.infra.adapter.competitor_repository import CompetitorRepository
from src.infra.adapter.booking_data_repository import BookingDataRepository
from src.infra.adapter.update_log_repository import UpdateLogRepository
from src.infra.adapter.bot_log_repository import BotLogRepository


class BaseTracker:
    def setup_driver(self):
        pass


class NausysTracker(BaseTracker):
    def __init__(self):
        super().__init__()
        self.base_url = "https://agency.nausys.com"
        self.driver = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logged_in = False
        self.db_conf = init_database()

    def setup_driver(self):
        try:
            self.logger.info("Driver kurulumu başlıyor...")
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service)
            self.driver.maximize_window()
            self.logger.info("Driver başarıyla kuruldu ve pencere maximize edildi.")
        except Exception as e:
            self.logger.exception("Driver kurulumu sırasında hata:", exc_info=True)
            raise

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
            self.logger.exception("Nausys login hatası:", exc_info=True)
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
            self.logger.exception("Booking list sayfasına giderken hata oluştu:", exc_info=True)
            raise

    def select_autocomplete_item(self, input_css, panel_css, text_to_type, text_to_click):
        try:
            input_box = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, input_css))
            )
            input_box.clear()
            input_box.send_keys(text_to_type)
            time.sleep(1)  # Bloklayıcı; eğer mümkünse bunu await asyncio.sleep(1) ile async hale getirin.
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
                WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable(desired_li))
                desired_li.click()
                self.logger.info(f"Autocomplete: '{text_to_type}' yazıldı, '{text_to_click}' seçildi.")
            else:
                self.logger.warning(f"Panelde '{text_to_click}' metnine sahip li bulunamadı.")
        except Exception as e:
            self.logger.exception("Autocomplete item seçerken hata:", exc_info=True)
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
            self.logger.exception("Charter firma seçerken hata:", exc_info=True)
            raise

    def get_yacht_ids_from_page(self) -> dict:
        try:
            yacht_ids = {}
            yacht_rows = WebDriverWait(self.driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "YachtRow"))
            )
            self.logger.info(f"Toplam {len(yacht_rows)} adet 'YachtRow' bulundu.")

            for row in yacht_rows:
                try:
                    row_body = row.find_element(By.CSS_SELECTOR, "[id^='y-']")
                    row_id = row_body.get_attribute('id')
                    yacht_id_match = re.search(r'y-(\d+)-', row_id)
                    yacht_name_element = row.find_element(By.CSS_SELECTOR, ".yachtName")
                    yacht_name = yacht_name_element.text.strip()
                    if yacht_id_match:
                        yacht_ids[yacht_name] = yacht_id_match.group(1)
                except Exception as row_error:
                    self.logger.exception("YachtRow işleme hatası:", exc_info=True)
                    continue
            self.logger.info(f"Toplam {len(yacht_ids)} adet YACHT ID bulundu: {yacht_ids}")
            return yacht_ids
        except Exception as e:
            self.logger.exception("Yacht ID'leri alınırken hata:", exc_info=True)
            return {}

    async def scrape_yacht_ids_and_save(self, competitor_name: str, company_search_text: str, company_click_text: str):
        self.logger.info(f"Scrape süreci başlatıldı: '{company_search_text}' / '{company_click_text}'")
        if not self.logged_in:
            if not self.login():
                self.logger.error("Login başarısız, yat ID'leri çekilemedi.")
                return []

        self.go_to_booking_list_page()
        self.select_charter_company_and_search(company_search_text, company_click_text)
        await asyncio.sleep(2)

        yacht_ids = self.get_yacht_ids_from_page()
        try:
            db_client = self.db_conf.db_session
            database = db_client["boat_tracker"]
            comp_repo = CompetitorRepository(database)
            await comp_repo.upsert_competitor_info(
                competitor_name=competitor_name,
                yacht_ids=yacht_ids,
                search_text=company_search_text,
                click_text=company_click_text
            )
            self.logger.info(f"[{competitor_name}] Çekilen YACHT ID'leri DB'ye kaydedildi: {yacht_ids}")
        except Exception as db_e:
            self.logger.exception("Rakip bilgisi güncellenirken hata:", exc_info=True)
        return yacht_ids

    def get_session_data(self):
        try:
            cookies = self.driver.get_cookies()
            jsessionid = next((c['value'] for c in cookies if c['name'] == 'JSESSIONID'), None)
            nult = next((c['value'] for c in cookies if c['name'] == 'nult'), None)
            bls = next((c['value'] for c in cookies if c['name'] == 'bls_53243141'), None)
            view_state = self.driver.execute_script("""
                return document.querySelector('input[name="javax.faces.ViewState"]').value;
            """)
            return jsessionid, view_state, nult, bls
        except Exception as e:
            self.logger.exception("Session data alma hatası:", exc_info=True)
            return None, None, None, None

    async def fetch_booking_details(self, yacht_id, period_from, period_to):
        """
        Belirtilen parametrelerle istek gönderilir. Eğer 30 saniyeden uzun süre cevap alınmazsa,
        max_retries (3) deneme yapılır. Her timeout durumunda DB'ye 'max_request_number_reached'
        hatası loglanır ve 1 saat beklenir. 3 denemeden sonra hala cevap alınamazsa None döndürülür.
        """
        max_retries = 3
        attempts = 0
        while attempts < max_retries:
            try:
                jsessionid, view_state, nult, bls = self.get_session_data()
                if not jsessionid or not view_state or not nult:
                    self.logger.error("Session bilgileri alınamadı!")
                    return None

                url = "https://agency.nausys.com/NauSYS-agency/app/yachtReservationDialog.xhtml"
                headers = {
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Encoding": "gzip, deflate, br",
                    "Accept-Language": "tr-TR,tr;q=0.9",
                    "Connection": "keep-alive",
                }
                cookies = {
                    "JSESSIONID": jsessionid,
                    "nult": nult,
                    "bls_5324314": bls
                }
                params = [
                    ("YachtReservationId", "-1"),
                    ("action", "newFromBookingList"),
                    ("displayAndEdit", "true"),
                    ("yachtReservationParams", yacht_id),
                    ("yachtReservationParams", self.format_date_for_api(period_from)),
                    ("yachtReservationParams", self.format_date_for_api(period_to)),
                    ("yachtReservationParams", "true"),
                    ("yachtReservationParams", ""),
                    ("yachtReservationParams", ""),
                    ("yachtReservationParams", ""),
                    ("yachtReservationParams", ""),
                ]
                # Bloklayıcı requests.get çağrısını ayrı thread'de çalıştırmak için:
                resp = await asyncio.to_thread(
                    requests.get,
                    url,
                    headers=headers,
                    cookies=cookies,
                    params=params,
                    timeout=30
                )
                if not resp.ok:
                    self.logger.error(f"API isteği başarısız: {resp.status_code}")
                    return None
                tree = html.fromstring(resp.content)
                xpaths = {
                    "discount_name": '//*[@id="yachtReservationDialogForm:tabView:discountGroup:contentTable:0:discountName"]',
                    "yacht_name": '//*[@id="yachtReservationDialogForm:tabView:j_idt109"]',
                    "company_name": '//*[@id="yachtReservationDialogForm:tabView:generalPanel"]/tbody/tr[3]/td[2]/div/div[1]/label',
                    "port_from": '//*[@id="yachtReservationDialogForm:tabView:generalPanel"]/tbody/tr[7]/td[2]/label',
                    "port_to": '//*[@id="yachtReservationDialogForm:tabView:generalPanel"]/tbody/tr[8]/td[2]/label',
                    "deposit": '//*[@id="yachtReservationDialogForm:tabView:generalPanel"]/tbody/tr[10]/td[2]/span[1]',
                    "discount_percent": '//*[@id="yachtReservationDialogForm:tabView:discountGroup:contentTable_data"]/tr/td[5]/span',
                    "list_price": '//*[@id="yachtReservationDialogForm:tabView:priceCalculationPanelGrid"]/tbody/tr[1]/td[2]/div/div/span[1]',
                    "discount": '//*[@id="yachtReservationDialogForm:tabView:priceCalculationPanelGrid"]/tbody/tr[1]/td[2]/div/div/span[3]/span[1]',
                    "total_price": '//*[@id="yachtReservationDialogForm:tabView:priceCalculationPanelGrid"]/tbody/tr[1]/td[2]/div/div/span[4]',
                    "commission_percent": '//*[@id="yachtReservationDialogForm:tabView:commissionPercent"]',
                    "commission": '//*[@id="yachtReservationDialogForm:tabView:priceCalculationPanelGrid"]/tbody/tr[2]/td[2]/div/div[2]/span[1]',
                    "client_price": '//*[@id="yachtReservationDialogForm:tabView:priceCalculationPanelGrid"]/tbody/tr[4]/td[2]/div/div/span[1]',
                    "agency_price": '//*[@id="yachtReservationDialogForm:tabView:priceCalculationPanelGrid"]/tbody/tr[5]/td[2]/div/div/span[1]',
                    "agency_income": '//*[@id="yachtReservationDialogForm:tabView:priceCalculationPanelGrid"]/tbody/tr[6]/td[2]/div/div/span[1]',
                    "total_advanced_payment": '//*[@id="yachtReservationDialogForm:tabView:priceCalculationPanelGrid"]/tbody/tr[7]/td[2]/div/div/span[1]',
                }
                results = {}
                for key, xp in xpaths.items():
                    elems = tree.xpath(xp)
                    if elems:
                        text_content = elems[0].text_content().strip()
                        results[key] = text_content
                    else:
                        results[key] = None
                        self.logger.warning(f"{key} isimli bilgi bulunamadı.")
                return results
            except requests.exceptions.Timeout:
                attempts += 1
                self.logger.error(f"max_request_number_reached for yacht_id {yacht_id}, attempt {attempts}")
                try:
                    db_client = self.db_conf.db_session
                    database = db_client["boat_tracker"]
                    update_log_repo = UpdateLogRepository(database)
                    await update_log_repo.create_one(update_log_repo.collection_name, {
                        "competitor": "N/A",
                        "yacht_id": yacht_id,
                        "last_update_date": datetime.now(),
                        "status": "error",
                        "error": "max_request_number_reached",
                        "timestamp": datetime.now()
                    })
                except Exception as log_ex:
                    self.logger.exception("Hata loglanırken hata oluştu:", exc_info=True)
                self.logger.info("1 saat bekleniyor, ardından tekrar denenecek...")
                await asyncio.sleep(3600)
            except Exception as e:
                self.logger.exception("Booking detayları çekerken beklenmeyen hata:", exc_info=True)
                return None
        # Eğer max_retries denendiyse ve hala sonuç alınamadıysa:
        self.logger.error(f"Max retries reached for yacht_id {yacht_id}. Bu gün için atlanacak.")
        return None

    @staticmethod
    def generate_weekly_dates(start_date_str="2025-04-12", end_date_str="2025-10-25"):
        try:
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
        except Exception as e:
            logging.exception("Haftalık periyot oluşturulurken hata:", exc_info=True)
            return []

    async def collect_data_and_save(self):
        """
        Her rakip için:
          - Aynı gün güncelleme yapılmış yacht ID’ler kontrol edilip atlanır.
          - Tüm rakipler arasında (global) 7 yat ID güncellendikten sonra 1 saat beklenir.
          - Her güncelleme sonucu (başarılı/hata) UpdateLogRepository aracılığıyla loglanır.
        """
        if not self.logged_in:
            if not self.login():
                self.logger.error("Login başarısız oldu, data toplanamıyor.")
                return

        try:
            db_client = self.db_conf.db_session
            database = db_client["boat_tracker"]
            book_repo = BookingDataRepository(database)
            update_log_repo = UpdateLogRepository(database)
            bot_log_repo = BotLogRepository(database)
        except Exception as e:
            self.logger.exception("DB bağlantısı oluşturulurken hata:", exc_info=True)
            return

        date_ranges = self.generate_weekly_dates()
        self.logger.info(f"Toplam {len(date_ranges)} haftalık periyot üretildi.")

        total_processed = 0
        start_date = datetime.now()
        today_dt = datetime.combine(date.today(), datetime.min.time())

        for competitor_name, competitor_data in COMPETITORS.items():
            if not competitor_data:
                continue

            self.logger.info(f"\nFirma: {competitor_name}, Veriler: {competitor_data}")
            yacht_ids_dict = competitor_data.get("yacht_ids", {})

            for yid in yacht_ids_dict.values():
                query = {
                    "competitor": competitor_name,
                    "yacht_id": yid,
                    "last_update_date": today_dt
                }
                try:
                    log_entry = await update_log_repo.find_one(update_log_repo.collection_name, query)
                except Exception as e:
                    self.logger.exception("Update log sorgusu sırasında hata:", exc_info=True)
                    log_entry = None

                if log_entry:
                    self.logger.info(f"Yacht id {yid} zaten güncellendi, atlanıyor.")
                    continue

                self.logger.info(f"-- Yat ID: {yid} güncelleniyor.")
                doc = {
                    "yacht_id": yid,
                    "last_update_date": today_dt,
                    "booking_periods": []
                }
                try:
                    for (p_from, p_to) in date_ranges:
                        try:
                            details = await self.fetch_booking_details(yid, p_from, p_to)
                        except Exception as inner_e:
                            self.logger.exception("fetch_booking_details sırasında hata:", exc_info=True)
                            details = None
                        if details:
                            doc["booking_periods"].append({
                                "period_from": p_from,
                                "period_to": p_to,
                                "details": [details]
                            })
                            self.logger.info(f"  * {p_from} -> {p_to} için veri eklendi.")
                        else:
                            self.logger.warning(f"  - {p_from} -> {p_to} için veri bulunamadı.")
                    await book_repo.save_daily_booking_data(competitor_name, [doc])
                    await update_log_repo.create_one(update_log_repo.collection_name, {
                        "competitor": competitor_name,
                        "yacht_id": yid,
                        "last_update_date": today_dt,
                        "status": "success",
                        "timestamp": datetime.now()
                    })
                except Exception as update_err:
                    self.logger.exception(f"Yacht id {yid} güncellenirken hata:", exc_info=True)
                    await update_log_repo.create_one(update_log_repo.collection_name, {
                        "competitor": competitor_name,
                        "yacht_id": yid,
                        "last_update_date": today_dt,
                        "status": "error",
                        "error": str(update_err),
                        "timestamp": datetime.now()
                    })
                total_processed += 1
                self.logger.info(f"Toplam güncellenen yat ID sayısı: {total_processed}")
                if total_processed % 7 == 0:
                    self.logger.info("7 yat ID güncellendi. 1 saat bekleniyor...")
                    try:
                        await asyncio.sleep(3600)
                    except asyncio.CancelledError:
                        self.logger.info("Sleep işlemi iptal edildi.")
                        break

        self.logger.info("Tüm rakipler için data toplama işlemi tamamlandı.")
        await bot_log_repo.create_one(bot_log_repo.collection_name, {
            "bot_id": 1,
            "status": "success",
            "last_update_date": datetime.now(),
            "timestamp": start_date
        })

    @staticmethod
    def format_date_for_api(date_str):
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d.%m.%Y %H:%M")
        except ValueError as e:
            logging.exception("Tarih formatlama hatası:", exc_info=True)
            return date_str


async def test_nausys_bot():
    logging.basicConfig(level=logging.INFO)
    bot = NausysTracker()
    try:
        await asyncio.to_thread(bot.setup_driver)
        if not bot.login():
            logging.error("Initial login failed. Exiting test.")
            return
        await bot.collect_data_and_save()
        logging.info("Tüm işlem tamamlandı.")
    except Exception as e:
        logging.exception("Test sırasında hata oluştu:", exc_info=True)
    finally:
        await asyncio.to_thread(time.sleep, 3)


if __name__ == "__main__":
    asyncio.run(test_nausys_bot())
