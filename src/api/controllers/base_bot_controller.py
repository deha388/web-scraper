from datetime import datetime
from typing import Dict
import threading
import time

class BaseBotController:
    _bots: Dict[str, Dict] = {}  # Platform bazlı bot durumlarını tut
    _lock = threading.Lock()

    @classmethod
    def start_bot(cls, platform: str):
        with cls._lock:
            if platform not in cls._bots or not cls._bots[platform].get('is_running', False):
                thread = threading.Thread(target=cls._run_bot, args=(platform,))
                cls._bots[platform] = {
                    'is_running': True,
                    'thread': thread,
                    'last_run': datetime.utcnow(),
                    'status': 'running'
                }
                thread.start()
                return True
            return False

    @classmethod
    def stop_bot(cls, platform: str):
        with cls._lock:
            if platform in cls._bots:
                cls._bots[platform]['is_running'] = False
                cls._bots[platform]['status'] = 'stopped'
                return True
            return False

    @classmethod
    def get_status(cls, platform: str):
        with cls._lock:
            return cls._bots.get(platform, {'status': 'not_started'})

    @staticmethod
    def _run_bot(platform: str):
        while BaseBotController._bots[platform]['is_running']:
            try:
                # Bot işlemleri burada yapılacak
                time.sleep(60)  # Her dakika kontrol et
            except Exception as e:
                BaseBotController._bots[platform]['status'] = f'error: {str(e)}'
                break 