import warnings
from dotenv import load_dotenv
from starlette.config import Config
from typing import Optional

warnings.filterwarnings("ignore", message="Config file '.env' not found.")

load_dotenv("local.env")

config = Config(".env")

APP_NAME: str = "Boat Price Tracker"
MONGO_IP: str = config('MONGO_IP', cast=str, default='localhost')
MONGO_PORT: int = config('MONGO_PORT', cast=int, default=27017)
MONGO_DB: str = config('MONGO_DB', cast=str, default='boat_tracker')
MONGO_USERNAME: Optional[str] = config('MONGO_USERNAME', cast=str, default='')
MONGO_PASSWORD: Optional[str] = config('MONGO_PASSWORD', cast=str, default='')

# Authentication settings
ADMIN_USERNAME: str = config('ADMIN_USERNAME', cast=str, default=None)
ADMIN_PASSWORD: str = config('ADMIN_PASSWORD', cast=str, default=None)
JWT_SECRET_KEY: str = config('JWT_SECRET_KEY', cast=str, default=None)
JWT_EXPIRE_MINUTES: int = config('JWT_EXPIRE_MINUTES', cast=int, default=None)
