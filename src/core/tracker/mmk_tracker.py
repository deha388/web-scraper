from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from src.core.tracker.base_tracker import BaseTracker

class MMKTracker(BaseTracker):
    def __init__(self):
        super().__init__()
        self.base_url = "https://portal.booking-manager.com/wbm2/app/login_register/"
        
    def login(self):
        if self.logged_in:
            self.logger.info("Zaten login durumundasınız, tekrar giriş yapılmadı.")
            return True
        try:
            self.driver.get(self.base_url)
            time.sleep(5)
            
            self.logger.info("Form elementlerini arıyorum...")
            username = self.wait_and_find_element(By.NAME, "login_email")
            password = self.wait_and_find_element(By.NAME, "login_password")
            
            self.logger.info("Kullanıcı bilgilerini giriyorum...")
            username.send_keys("sulhicanbilgin@gmail.com")
            password.send_keys("Can260294")
            
            login_button = self.wait_for_clickable(By.CSS_SELECTOR, "input[type='submit'][value='Login']")
            self.logger.info("Login butonuna tıklıyorum...")
            self.safe_click(login_button)
            
            WebDriverWait(self.driver, 10).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CLASS_NAME, "main-container")),
                    EC.presence_of_element_located((By.CLASS_NAME, "navbar-container"))
                )
            )
            
            self.logger.info("MMK Booking Manager'a başarıyla giriş yapıldı")
            self.logged_in = True
            time.sleep(10)
            return True
            
        except Exception as e:
            self.logger.error(f"MMK login hatası: {str(e)}")
            self.logger.error(f"Hata detayı: {type(e).__name__}")
            return False

if __name__ == "__main__":
    try:
        tracker = MMKTracker()
        tracker.setup_driver()
        login_success = tracker.login()
        print(f"Login başarılı mı: {login_success}")
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")
    finally:
        if tracker:
            tracker.cleanup() 