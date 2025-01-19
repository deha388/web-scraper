from abc import ABC, abstractmethod
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

class BaseTracker(ABC):
    def __init__(self):
        self.driver = None
        self.logger = logging.getLogger(self.__class__.__name__)
        self.base_url = None
        self.logged_in = False

    def setup_driver(self):
        """Ortak driver kurulum fonksiyonu"""
        self.logger.info("Driver kurulumu başlıyor...")
        options = webdriver.ChromeOptions()
        # Docker için gerekli argümanlar
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)
        self.logger.info("Driver başarıyla kuruldu.")

    @abstractmethod
    def login(self):
        """Her bot kendi login mantığını implement etmeli"""
        pass

    def wait_and_find_element(self, by, value, timeout=10):
        """Ortak element bekleme ve bulma fonksiyonu"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def wait_for_clickable(self, by, value, timeout=10):
        """Ortak tıklanabilir element bekleme fonksiyonu"""
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )

    def safe_click(self, element):
        """Ortak güvenli tıklama fonksiyonu"""
        try:
            WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(element)
            )
            element.click()
            return True
        except Exception as e:
            self.logger.error(f"Tıklama hatası: {str(e)}")
            return False

    def cleanup(self):
        """Ortak temizleme fonksiyonu"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.logged_in = False
