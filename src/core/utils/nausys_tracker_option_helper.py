import time
import logging
import os
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
from selenium.common.exceptions import TimeoutException


class BaseTracker:
    def setup_driver(self):
        pass


class NausysTracker(BaseTracker):
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
            username.send_keys("user@SAAMO")
            password.send_keys("sail1234")
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
            for li in all_li:
                self.logger.info(f"  -> li metni: '{li.text}'")
            desired_li = None
            for li in all_li:
                if text_to_click in li.text:
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

    def select_charter_company_and_search(self):
        try:
            self.logger.info("Charter company seçiliyor...")
            self.select_autocomplete_item(
                input_css="input[id$='charterCompanyAutocompleteComponentId2_input']",
                panel_css="span[id$='charterCompanyAutocompleteComponentId2_panel']",
                text_to_type="Rudder & Moor",
                text_to_click="rudder&moor"
            )
            time.sleep(1)
            search_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[id$='searchBtn']"))
            )
            search_button.click()
            time.sleep(5)
        except Exception as e:
            self.logger.error(f"Hata: {str(e)}")
            raise

    def handle_create_option_popup(self):
        try:
            time.sleep(3)
            get_iframe_src = """
                var iframe = document.querySelector('div[id$="newBookingCommand_dlg"] iframe');
                return iframe ? iframe.src : '';
            """
            iframe_src = self.driver.execute_script(get_iframe_src)
            if iframe_src:
                self.driver.get(iframe_src)
                time.sleep(2)
                booking_data = {}
                try:
                    period_from_date = self.driver.find_element(By.CSS_SELECTOR, "#yachtReservationDialogForm\\:tabView\\:periodFrom_input").get_attribute("value")
                    period_from_time = self.driver.find_element(By.CSS_SELECTOR, "#yachtReservationDialogForm\\:tabView\\:checkInTimeOutput").text
                    period_to_date = self.driver.find_element(By.CSS_SELECTOR, "#yachtReservationDialogForm\\:tabView\\:periodTo_input").get_attribute("value")
                    period_to_time = self.driver.find_element(By.CSS_SELECTOR, "#yachtReservationDialogForm\\:tabView\\:checkOutTimeOutput").text
                    booking_data['period'] = {
                        'from': f"{period_from_date} {period_from_time}",
                        'to': f"{period_to_date} {period_to_time}"
                    }
                    from_location = self.driver.find_element(By.XPATH, "//td[@class='label']/label[text()='From:']/../../td[@class='field']/label").text
                    to_location = self.driver.find_element(By.XPATH, "//td[@class='label']/label[text()='To:']/../../td[@class='field']/label").text
                    booking_data['location'] = {
                        'from': from_location,
                        'to': to_location
                    }
                    list_price_element = self.driver.find_element(By.XPATH, "//td[@class='label']/label[text()='List price:']/../../td[@class='field']")
                    list_price = list_price_element.find_elements(By.CSS_SELECTOR, "span")[0].text + " " + list_price_element.find_elements(By.CSS_SELECTOR, "span")[1].text
                    total_advanced_element = self.driver.find_element(By.XPATH, "//label[contains(text(), 'Total advanced payment:')]/../../td//span[@class='bold']")
                    total_advanced = total_advanced_element.text + " " + total_advanced_element.find_element(By.XPATH, "following-sibling::span").text
                    booking_data['prices'] = {
                        'list_price': list_price,
                        'total_advanced_payment': total_advanced
                    }
                    json_file_path = 'booking_options.txt'
                    with open(json_file_path, 'a', encoding='utf-8') as f:
                        json.dump(booking_data, f, indent=2, ensure_ascii=False)
                        f.write("\n")
                except Exception as extract_error:
                    self.logger.error(f"Hata: {str(extract_error)}")
                self.driver.back()
            close_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".ui-dialog-titlebar-close"))
            )
            close_button.click()
        except Exception as e:
            self.logger.error(f"Hata: {str(e)}")
            try:
                self.driver.execute_script("""
                    var closeButtons = document.querySelectorAll(".ui-dialog-titlebar-close");
                    if (closeButtons.length > 0) closeButtons[0].click();
                """)
            except:
                pass

    def get_session_data(self):
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
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
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
                                    discounted_price = big_price.get_text(strip=True) if big_price else "N/A"
                                    if small_price:
                                        small_price_text = small_price.get_text(strip=True)
                                        original_price_match = re.search(r'\(([\d.,]+)', small_price_text)
                                        original_price = f"{original_price_match.group(1)} EUR" if original_price_match else "N/A"
                                        discount_match = re.search(r'-> (\d+) %', small_price_text)
                                        discount_percentage = f"{discount_match.group(1)}%" if discount_match else None
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

    def get_yacht_ids(self):
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

    def initialize_session(self):
        if not self.logged_in:
            success = self.login()
            if not success:
                self.logger.error("Login başarısız!")
                return None, None
        jsessionid, view_state = self.get_session_data()
        if not jsessionid or not view_state:
            self.logger.error("Session bilgileri alınamadı!")
            return None, None
        return jsessionid, view_state

    def generate_weekly_dates(self, start_date_str="2025-04-12", end_date_str="2025-10-25"):
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

    def process_all_yachts(self):
        jsessionid, view_state = self.initialize_session()
        if not jsessionid or not view_state:
            return
        self.go_to_booking_list_page()
        self.select_charter_company_and_search()
        time.sleep(5)
        date_pairs = self.generate_weekly_dates()
        company_results = {}
        for company, yacht_ids in self.YACHT_IDS.items():
            self.logger.info(f"\n{company} firması için işlemler başlıyor...")
            company_results[company] = {}
            for yacht_id in yacht_ids:
                self.logger.info(f"\nYat ID {yacht_id} için işlemler başlıyor...")
                company_results[company][yacht_id] = []
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
                            company_results[company][yacht_id].append(period_result)
                            self.logger.info("Booking detayları başarıyla kaydedildi.")
                        else:
                            self.logger.warning(f"Yacht ID {yacht_id} için {period_from} - {period_to} aralığında veri alınamadı.")
                        time.sleep(1)
                    except Exception as e:
                        self.logger.error(f"Hata oluştu: {str(e)}")
                        continue
        with open('booking_results.txt', 'w', encoding='utf-8') as f:
            json.dump(company_results, f, indent=2, ensure_ascii=False)


def test_nausys_bot():
    logging.basicConfig(level=logging.INFO)
    try:
        bot = NausysTracker()
        bot.setup_driver()
        logging.info("Driver setup complete")
        bot.process_all_yachts()
        logging.info("İşlemler tamamlandı.")
    except Exception as e:
        logging.error(f"Test sırasında hata oluştu: {str(e)}")
        raise
    finally:
        time.sleep(5)
        if 'bot' in locals() and hasattr(bot, 'driver'):
            bot.driver.quit()




if __name__ == "__main__":
    test_nausys_bot()
