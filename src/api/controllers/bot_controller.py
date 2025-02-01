import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from src.infra.config.init_database import init_database
from src.api.dto.bot_dto import BotStatus, BotType, BotStatusResponse

from src.core.tracker.nausys_tracker import NausysTracker

logger = logging.getLogger(__name__)


class BotInstance:
    def __init__(self):
        self.status: BotStatus = BotStatus.STOPPED
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.task: Optional[asyncio.Task] = None
        self.message: str = ""
        self.tracker: Optional[NausysTracker] = None


class BotController:
    def __init__(self, db):
        if db is None:
            db = init_database()
        self.db = db
        self.bots: Dict[BotType, BotInstance] = {BotType.NAUSYS: BotInstance()}

    async def start_bot(self, bot_type: BotType) -> BotStatusResponse:
        bot_instance = self.bots[bot_type]

        if bot_instance.status == BotStatus.RUNNING:
            return BotStatusResponse(
                bot_type=bot_type,
                status=bot_instance.status,
                message="Bot is already running",
                last_run=bot_instance.last_run,
                next_run=bot_instance.next_run
            )

        bot_instance.status = BotStatus.RUNNING
        bot_instance.message = "Bot started. Will run daily at 00:00."
        if bot_instance.tracker is None:
            bot_instance.tracker = NausysTracker()
            bot_instance.tracker.setup_driver()
            success = bot_instance.tracker.login()
            if not success:
                bot_instance.status = BotStatus.ERROR
                bot_instance.message = "Initial login failed."
                return BotStatusResponse(
                    bot_type=bot_type,
                    status=bot_instance.status,
                    message=bot_instance.message,
                    last_run=None,
                    next_run=None
                )

        bot_instance.task = asyncio.create_task(self._daily_scheduler(bot_type))
        await self._run_daily_job(bot_type)

        return BotStatusResponse(
            bot_type=bot_type,
            status=bot_instance.status,
            message="Bot has started successfully. Next run at 00:00",
            last_run=bot_instance.last_run,
            next_run=bot_instance.next_run
        )

    async def _daily_scheduler(self, bot_type: BotType):

        bot_instance = self.bots[bot_type]
        while bot_instance.status == BotStatus.RUNNING:
            now = datetime.now()
            next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            bot_instance.next_run = next_midnight

            seconds_to_wait = (next_midnight - now).total_seconds()
            logger.info(f"[{bot_type}] Bot will sleep until {next_midnight} (~{int(seconds_to_wait)}s).")

            try:
                await asyncio.sleep(seconds_to_wait)
            except asyncio.CancelledError:
                logger.info(f"[{bot_type}] Bot daily scheduler task cancelled.")
                break

            if bot_instance.status == BotStatus.RUNNING:
                await self._run_daily_job(bot_type)

    async def _run_daily_job(self, bot_type: BotType):

        bot_instance = self.bots[bot_type]
        if bot_instance.tracker is None:
            logger.error("Tracker instance yok, veri çekme atlandı.")
            return

        if not bot_instance.tracker.logged_in:
            logger.info("Oturum düşmüş gibi görünüyor; tekrar login denenecek...")
            ok = bot_instance.tracker.login()
            if not ok:
                bot_instance.status = BotStatus.ERROR
                bot_instance.message = "Login failed during daily run."
                logger.error("Login failed, daily job iptal.")
                return

        try:
            await bot_instance.tracker.collect_data_and_save()
            bot_instance.last_run = datetime.now()
            bot_instance.message = f"Last run at {bot_instance.last_run}"
            logger.info(f"[{bot_type}] Bot daily run completed at {bot_instance.last_run}")

        except Exception as e:
            bot_instance.status = BotStatus.ERROR
            bot_instance.message = f"Error while daily job: {str(e)}"
            logger.error(f"[{bot_type}] BOT ERROR: {e}", exc_info=True)

    async def stop_bot(self, bot_type: BotType) -> BotStatusResponse:

        bot_instance = self.bots[bot_type]
        if bot_instance.status == BotStatus.RUNNING:
            bot_instance.status = BotStatus.STOPPED
            if bot_instance.task:
                bot_instance.task.cancel()
                bot_instance.task = None
            bot_instance.message = "Bot was stopped manually."
            logger.info(f"[{bot_type}] Bot stopped manually.")
            if bot_instance.tracker and bot_instance.tracker.driver:
                bot_instance.tracker.driver.quit()
            bot_instance.tracker = None
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
