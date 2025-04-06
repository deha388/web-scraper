import warnings
import os
from dotenv import load_dotenv
from starlette.config import Config
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Try to load environment variables from .env file
if os.path.exists(".env"):
    load_dotenv(".env")
    logger.info("Loaded environment variables from .env file")
else:
    warnings.warn("Config file '.env' not found. Using environment variables or defaults.")

config = Config(".env")

APP_NAME: str = config('APP_NAME', cast=str, default='Boat Price Tracker')
MONGO_IP: str = config('MONGO_IP', cast=str, default='localhost')
MONGO_PORT: int = config('MONGO_PORT', cast=int, default=27017)
MONGO_DB: str = config('MONGO_DB', cast=str, default='boat_tracker')
MONGO_USERNAME: Optional[str] = config('MONGO_USERNAME', cast=str, default='')
MONGO_PASSWORD: Optional[str] = config('MONGO_PASSWORD', cast=str, default='')

# Authentication settings
ADMIN_USERNAME: str = config('ADMIN_USERNAME', cast=str, default=None)
ADMIN_PASSWORD: str = config('ADMIN_PASSWORD', cast=str, default=None)
JWT_SECRET_KEY: str = config('JWT_SECRET_KEY', cast=str, default=None)
JWT_EXPIRE_MINUTES: int = config('JWT_EXPIRE_MINUTES', cast=int, default=1440)

# MMK settings
MMK_USERNAME: str = config('MMK_USERNAME', cast=str, default="")
MMK_PASSWORD: str = config('MMK_PASSWORD', cast=str, default="")

# Nausys settings
NAUSYS_USERNAME: str = config('NAUSYS_USERNAME', cast=str, default="")
NAUSYS_PASSWORD: str = config('NAUSYS_PASSWORD', cast=str, default="")

# Log if any critical variables are missing
if not JWT_SECRET_KEY:
    logger.warning("JWT_SECRET_KEY is not set. This is a security risk in production!")
if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    logger.warning("Admin credentials are not set. Authentication might not work properly!")
if not MMK_USERNAME or not MMK_PASSWORD:
    logger.warning("MMK credentials are not set. MMK login might not work properly!")
if not NAUSYS_USERNAME or not NAUSYS_PASSWORD:
    logger.warning("Nausys credentials are not set. Nausys login might not work properly!")
