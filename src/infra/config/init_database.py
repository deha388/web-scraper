from urllib.parse import quote_plus
import logging

from src.infra.config.database import DatabaseConfig
from src.infra.config.settings import (
    MONGO_IP,
    MONGO_PORT,
    MONGO_USERNAME,
    MONGO_PASSWORD,
    MONGO_DB,
)

logger = logging.getLogger(__name__)


def init_database() -> DatabaseConfig:
    db_conf = DatabaseConfig()
    
    try:
        if MONGO_USERNAME and MONGO_PASSWORD:
            username = quote_plus(MONGO_USERNAME)
            password = quote_plus(MONGO_PASSWORD)
            connection_string = f"mongodb://{username}:{password}@{MONGO_IP}:{MONGO_PORT}/{MONGO_DB}"
            logger.info(f"Connecting to MongoDB with authentication at {MONGO_IP}:{MONGO_PORT}")
        else:
            connection_string = f"mongodb://{MONGO_IP}:{MONGO_PORT}/{MONGO_DB}"
            logger.info(f"Connecting to MongoDB without authentication at {MONGO_IP}:{MONGO_PORT}")
        
        db_conf.database_url = connection_string

        errors = db_conf.check()
        if errors:
            for err in errors:
                logger.error(err)
            raise ValueError("Veritabanı bağlantısı hatası.")
        
        return db_conf
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise
