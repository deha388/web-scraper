from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import bot, prices
from infra.mongodb import MongoDB
from core.config import settings

app = FastAPI(title=settings.APP_NAME)

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB bağlantısı
@app.on_event("startup")
async def startup_db_client():
    await MongoDB.connect_db()

@app.on_event("shutdown")
async def shutdown_db_client():
    await MongoDB.close_db()

# Route'ları ekle
app.include_router(bot.router, prefix="/api/bot", tags=["bot"])
app.include_router(prices.router, prefix="/api/prices", tags=["prices"])
