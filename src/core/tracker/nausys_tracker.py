from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_tracker import BaseTracker

class NausysTracker(BaseTracker):
    def __init__(self):
        super().__init__()
        self.base_url = "https://agency.nausys.com"
        
    def login(self):
        try:
            self.driver.get(self.base_url)
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
            )
            
            # Login form elementlerini bul
            username = self.driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            password = self.driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            
            username.send_keys("********")
            password.send_keys("********")
            
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".main-content"))
            )
            
            self.logger.info("Nausys'e başarıyla giriş yapıldı")
            return True
            
        except Exception as e:
            self.logger.error(f"Nausys login hatası: {str(e)}")
            return False 