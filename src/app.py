from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.api.routes import auth, bot, price, competitor
from src.infra.config.settings import MONGO_IP, MONGO_PORT, MONGO_DB, MONGO_USERNAME, MONGO_PASSWORD
from src.infra.config.database import config
from src.infra.config.init_database import init_database
from src.api.controllers.bot_controller import BotController
from fastapi.middleware.cors import CORSMiddleware
from src.origins import get_origins
import logging
from urllib.parse import quote_plus

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
        db = init_database()
        app.state.db = db
        app.state.bot_controller = BotController(db)
        logger.info("Connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        raise e

    yield

    # Shutdown
    try:
        if hasattr(app.state.db, "close"):
            app.state.db.close()
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
    if MONGO_USERNAME and MONGO_PASSWORD:
        username = quote_plus(MONGO_USERNAME)
        password = quote_plus(MONGO_PASSWORD)
        database_url = f"mongodb://{username}:{password}@{MONGO_IP}:{MONGO_PORT}/{MONGO_DB}"
    else:
        database_url = f"mongodb://{MONGO_IP}:{MONGO_PORT}/{MONGO_DB}"
    
    config.database_url = database_url
    config.db_session

    app.add_middleware(CORSMiddleware, allow_origins=get_origins(), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

    # Include routers with prefix
    app.include_router(auth.router, prefix=PREFIX, tags=['Authentication'])
    app.include_router(bot.router, prefix=PREFIX, tags=['Bot Control'])
    app.include_router(price.router, prefix=PREFIX, tags=['Price'])
    app.include_router(competitor.router, prefix=PREFIX, tags=['Competitor'])

    return app
