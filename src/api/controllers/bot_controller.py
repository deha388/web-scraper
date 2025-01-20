# src/api/controllers/bot_controller.py
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

from src.api.dto.bot_dto import BotStatus, BotType, BotStatusResponse
from src.infra.config.init_database import init_database
from src.core.tracker.nausys_tracker import NausysTracker

logger = logging.getLogger(__name__)


class BotInstance:
    def __init__(self):
        self.status: BotStatus = BotStatus.STOPPED
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.task: Optional[asyncio.Task] = None
        self.message: str = ""


class BotController:
    def __init__(self, db=None):
        # Projenizde "db" parametresini kullanıyorsanız,
        # app.state.db vs. ile gelebilir. Gerekmezse init_database() yapabilirsiniz.
        if db is None:
            db = init_database()
        self.db = db

        self.bots: Dict[BotType, BotInstance] = {
            BotType.NAUSYS: BotInstance(),
            BotType.MMK: BotInstance()  # ileride başka bot ekleyebilirsiniz
        }

    async def start_bot(self, bot_type: BotType, interval_minutes: int = 60) -> BotStatusResponse:
        """
        Botu başlat:
         - Hemen bir kere collect_data_and_save (eksik varsa doldursun)
         - Sonra her gece 00:00'da da tekrarla
        """
        bot_instance = self.bots[bot_type]
        if bot_instance.status == BotStatus.RUNNING:
            return BotStatusResponse(
                bot_type=bot_type,
                status=bot_instance.status,
                message="Bot is already running",
                last_run=bot_instance.last_run,
                next_run=bot_instance.next_run
            )

        # Başlatırken ilk çekim:
        tracker = NausysTracker()
        tracker.setup_driver()
        await tracker.collect_data_and_save()
        tracker.driver.quit()

        # Ardından RUNNING mod + gece 00:00 döngüsü
        bot_instance.status = BotStatus.RUNNING
        bot_instance.message = f"Bot started. Will run daily at 00:00"
        bot_instance.task = asyncio.create_task(self.run_nausys_daily(bot_type))

        return BotStatusResponse(
            bot_type=bot_type,
            status=bot_instance.status,
            message="Nausys bot has started successfully",
            last_run=bot_instance.last_run,
            next_run=bot_instance.next_run
        )

    async def run_nausys_daily(self, bot_type: BotType):
        """
        Arkaplan döngü: Her gece 00:00'da collect_data_and_save tetikler.
        """
        bot_instance = self.bots[bot_type]
        while bot_instance.status == BotStatus.RUNNING:
            now = datetime.now()
            next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            seconds_to_wait = (next_midnight - now).total_seconds()
            bot_instance.next_run = next_midnight

            logger.info(f"[{bot_type}] Bot will sleep until {next_midnight} (about {seconds_to_wait} seconds).")
            try:
                await asyncio.sleep(seconds_to_wait)
            except asyncio.CancelledError:
                logger.info(f"[{bot_type}] Bot task cancelled.")
                break

            if bot_instance.status != BotStatus.RUNNING:
                break

            try:
                logger.info(f"[{bot_type}] Running collect_data_and_save...")
                tracker = NausysTracker()
                tracker.setup_driver()
                await tracker.collect_data_and_save()
                tracker.driver.quit()

                bot_instance.last_run = datetime.now()
                bot_instance.message = f"Last run at {bot_instance.last_run}"
                logger.info(f"[{bot_type}] Bot run completed at {bot_instance.last_run}")

            except Exception as e:
                bot_instance.status = BotStatus.ERROR
                bot_instance.message = f"Error: {str(e)}"
                logger.error(f"[{bot_type}] BOT ERROR: {e}", exc_info=True)
                break

    async def stop_bot(self, bot_type: BotType) -> BotStatusResponse:
        bot_instance = self.bots[bot_type]
        if bot_instance.status == BotStatus.RUNNING:
            bot_instance.status = BotStatus.STOPPED
            if bot_instance.task:
                bot_instance.task.cancel()
                bot_instance.task = None
            bot_instance.message = "Bot was stopped manually."
        else:
            bot_instance.message = "Bot is already stopped."

        return BotStatusResponse(
            bot_type=bot_type,
            status=bot_instance.status,
            message=bot_instance.message,
            last_run=bot_instance.last_run,
            next_run=bot_instance.next_run
        )

    async def get_bot_status(self, bot_type: BotType) -> BotStatusResponse:
        bot_instance = self.bots[bot_type]
        return BotStatusResponse(
            bot_type=bot_type,
            status=bot_instance.status,
            message=bot_instance.message,
            last_run=bot_instance.last_run,
            next_run=bot_instance.next_run
        )
