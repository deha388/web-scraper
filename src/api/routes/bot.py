from fastapi import APIRouter, HTTPException
from core.bot.nausys import NausysTracker
from core.bot.mmk import MMKTracker
from core.logger import logger

router = APIRouter()
bot_instance = None

@router.post("/start")
async def start_bot():
    global bot_instance
    try:
        if bot_instance is None:
            # İlk önce Nausys'e bağlan
            nausys = NausysTracker()
            nausys.setup_driver()
            if not nausys.login():
                raise HTTPException(status_code=500, detail="Nausys login failed")
            
            # Sonra MMK'ya bağlan
            mmk = MMKTracker()
            mmk.setup_driver()
            if not mmk.login():
                raise HTTPException(status_code=500, detail="MMK login failed")
            
            bot_instance = {"nausys": nausys, "mmk": mmk}
            return {"status": "success", "message": "Bot started successfully"}
    except Exception as e:
        logger.error(f"Bot start error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_bot():
    global bot_instance
    try:
        if bot_instance:
            bot_instance["nausys"].close()
            bot_instance["mmk"].close()
            bot_instance = None
            return {"status": "success", "message": "Bot stopped successfully"}
        return {"status": "warning", "message": "Bot was not running"}
    except Exception as e:
        logger.error(f"Bot stop error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 