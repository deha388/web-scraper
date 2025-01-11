from abc import ABC, abstractmethod
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging


class BaseTracker(ABC):
    def __init__(self):
        self.driver = None
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)

    def setup_driver(self):
        options = webdriver.ChromeOptions()
        # Docker için headless ve diğer argümanlar
        if self.is_running_in_docker():
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
        else:
            # Lokal geliştirme için pencere boyutu
            options.add_argument('--start-maximized')

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)

    def is_running_in_docker(self):
        """Docker içinde çalışıp çalışmadığını kontrol et"""
        try:
            with open('/proc/1/cgroup', 'r') as f:
                return 'docker' in f.read()
        except:
            return False

    @abstractmethod
    def login(self):
        pass

    def close(self):
        if self.driver:
            self.driver.quit()
