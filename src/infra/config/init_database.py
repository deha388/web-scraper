from urllib.parse import quote_plus

from src.infra.config.database import DatabaseConfig
from src.infra.config.settings import (
    MONGO_IP,
    MONGO_PORT,
    MONGO_USERNAME,
    MONGO_PASSWORD,
    MONGO_DB,
)


def init_database() -> DatabaseConfig:
    db_conf = DatabaseConfig()
    if MONGO_USERNAME and MONGO_PASSWORD:
        username = quote_plus(MONGO_USERNAME)
        password = quote_plus(MONGO_PASSWORD)
        db_conf.database_url = f"mongodb://{username}:{password}@{MONGO_IP}:{MONGO_PORT}/{MONGO_DB}"
    else:
        db_conf.database_url = f"mongodb://{MONGO_IP}:{MONGO_PORT}/{MONGO_DB}"

    errors = db_conf.check()
    if errors:
        for err in errors:
            print(err)
        raise ValueError("Veritabanı bağlantısı hatası.")

    return db_conf
