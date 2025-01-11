from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_tracker import BaseTracker
import time

class MMKTracker(BaseTracker):
    def __init__(self):
        super().__init__()
        self.base_url = "https://portal.booking-manager.com/wbm2/app/login_register/"
        
    def login(self):
        try:
            self.driver.get(self.base_url)
            
            time.sleep(5)
            
            self.logger.info("Form elementlerini arıyorum...")
            
            username = self.driver.find_element(By.NAME, "login_email")
            password = self.driver.find_element(By.NAME, "login_password")
            
            self.logger.info("Kullanıcı bilgilerini giriyorum...")
            username.send_keys("********")
            password.send_keys("********")
            
            login_button = self.driver.find_element(By.CSS_SELECTOR, "input[type='submit'][value='Login']")
            
            self.logger.info("Login butonuna tıklıyorum...")
            login_button.click()
            
            WebDriverWait(self.driver, 10).until(
                EC.any_of(
                    EC.presence_of_element_located((By.CLASS_NAME, "main-container")),
                    EC.presence_of_element_located((By.CLASS_NAME, "navbar-container"))
                )
            )
            
            self.logger.info("MMK Booking Manager'a başarıyla giriş yapıldı")
            time.sleep(10)
            return True
            
        except Exception as e:
            self.logger.error(f"MMK login hatası: {str(e)}")
            self.logger.error(f"Hata detayı: {type(e).__name__}")
            return False 