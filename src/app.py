from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.routes import auth, bot, prices
from src.infra.config.settings import MONGO_IP, MONGO_PORT, MONGO_DB, MONGO_USERNAME, MONGO_PASSWORD
from src.infra.config.database import config
from src.infra.config.init_database import init_database
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PREFIX = "/api/v1"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    try:
        # Initialize database
        db = init_database()
        app.state.db = db
        logger.info("Connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise e

    yield

    # Shutdown
    try:
        logger.info("Closed MongoDB connection")
    except Exception as e:
        logger.error(f"Error closing MongoDB connection: {str(e)}")


def create_app():
    app = FastAPI(
        lifespan=lifespan,
        title="Boat Price Tracker API",
        description="Boat price tracking and comparison system",
        version="1.0.0",
        openapi_url="/openapi.json",
        docs_url="/",
        redoc_url="/redoc"
    )

    # Configure your database
    #database_url = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_IP}:{MONGO_PORT}?replicaSet=rs0&readPreference=secondaryPreferred&retryWrites=false"
    database_url = f"mongodb://{MONGO_IP}:{MONGO_PORT}/{MONGO_DB}"
    config.database_url = database_url
    config.db_session

    # Include routers with prefix
    app.include_router(auth.router, prefix=PREFIX, tags=['Authentication'])
    app.include_router(bot.router, prefix=PREFIX, tags=['Bot Control'])
    app.include_router(prices.router, prefix=PREFIX, tags=['Price Tracking'])

    return app
