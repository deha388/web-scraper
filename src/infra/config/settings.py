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
MONGODB_DB_NAME: str = config('MONGO_DB', cast=str, default='boat_tracker')
MONGO_USERNAME: Optional[str] = config('MONGO_USERNAME', cast=str, default='')
MONGO_PASSWORD: Optional[str] = config('MONGO_PASSWORD', cast=str, default='')

# Authentication settings
ADMIN_USERNAME: str = "admin"
ADMIN_PASSWORD: str = "admin123"
JWT_SECRET_KEY: str = "your-super-secret-key-here"
JWT_EXPIRE_MINUTES: int = 1440
