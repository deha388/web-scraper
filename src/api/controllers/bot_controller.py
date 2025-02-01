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
        self.last_started: Optional[datetime] = None
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.task: Optional[asyncio.Task] = None
        self.message: str = ""
        self.tracker: Optional[NausysTracker] = None


class BotController:
    def __init__(self, db=None):
        if db is None:
            from src.infra.config.init_database import init_database
            db = init_database()
        self.db = db
        self.bots: Dict[BotType, BotInstance] = {BotType.NAUSYS: BotInstance()}

    async def start_bot(self, bot_type: BotType) -> BotStatusResponse:
        bot_instance = self.bots[bot_type]

        if bot_instance.status == BotStatus.RUNNING:
            return BotStatusResponse(
                bot_type=bot_type,
                status=bot_instance.status,
                message="Bot is already running.",
                last_run=bot_instance.last_run,
                next_run=bot_instance.next_run,
                bot_last_started=bot_instance.last_started,
            )

        bot_instance.status = BotStatus.RUNNING
        bot_instance.last_started = datetime.now()
        bot_instance.message = "Bot started. Running daily jobs."

        # Eğer tracker henüz oluşturulmamışsa oluştur ve login dene.
        if bot_instance.tracker is None:
            bot_instance.tracker = NausysTracker()
            bot_instance.tracker.setup_driver()
            # Eğer login başarısızsa, bot hata mesajı versin ama çalışmayı kesmesin.
            if not bot_instance.tracker.login():
                bot_instance.message = "Initial login failed. Bot will retry on next scheduled run."
                logger.error("Initial login failed.")
                # Bot status yine RUNNING olarak kalıyor; sonraki güncelleme zamanı gelince tekrar login denenecek.
        # Bot arka plan görevini (daily scheduler) başlatıyoruz.
        bot_instance.task = asyncio.create_task(self._daily_scheduler(bot_type))
        # İlk çalıştırmayı da hemen yapıyoruz.
        await self._run_daily_job(bot_type)

        return BotStatusResponse(
            bot_type=bot_type,
            status=bot_instance.status,
            message=bot_instance.message,
            last_run=bot_instance.last_run,
            next_run=bot_instance.next_run,
            bot_last_started=bot_instance.last_started,
        )

    async def _daily_scheduler(self, bot_type: BotType):
        bot_instance = self.bots[bot_type]
        while bot_instance.status == BotStatus.RUNNING:
            now = datetime.now()
            # Gelecek günün 00:00:00 zamanı
            next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            bot_instance.next_run = next_midnight
            seconds_to_wait = (next_midnight - now).total_seconds()
            logger.info(f"[{bot_type}] Sleeping until {next_midnight} (~{int(seconds_to_wait)}s).")
            try:
                await asyncio.sleep(seconds_to_wait)
            except asyncio.CancelledError:
                logger.info(f"[{bot_type}] Daily scheduler cancelled.")
                break

            if bot_instance.status == BotStatus.RUNNING:
                await self._run_daily_job(bot_type)

    async def _run_daily_job(self, bot_type: BotType):
        bot_instance = self.bots[bot_type]
        if bot_instance.tracker is None:
            logger.error("Tracker instance not found; daily job skipped.")
            return

        if not bot_instance.tracker.logged_in:
            logger.info("Session appears to be expired; attempting re-login...")
            if not bot_instance.tracker.login():
                bot_instance.message = "Login failed during daily run. Will retry at next scheduled time."
                logger.error("Login failed during daily run.")
                # Hata durumunu DB'ye loglamak için UpdateLogRepository kullanılabilir.
                return

        try:
            # Eğer tracker kodunuzun bazı bloklayıcı kısımları varsa,
            # bunları ayrı thread'de çalıştırmak için asyncio.to_thread kullanabilirsiniz.
            await bot_instance.tracker.collect_data_and_save()
            bot_instance.last_run = datetime.now()
            bot_instance.message = f"Daily run completed successfully at {bot_instance.last_run}."
            logger.info(f"[{bot_type}] Daily run completed at {bot_instance.last_run}.")
        except Exception as e:
            # Hata durumunda bot status RUNNING olarak kalmaya devam eder.
            bot_instance.message = f"Error during daily job: {str(e)}. Will retry at next scheduled time."
            logger.error(f"[{bot_type}] Error during daily job: {e}", exc_info=True)
            # Burada hatayı UpdateLogRepository ile DB'ye kaydedebilirsiniz.
            from src.infra.adapter.update_log_repository import UpdateLogRepository
            db_client = self.db.db_session
            database = db_client["boat_tracker"]
            update_log_repo = UpdateLogRepository(database)
            await update_log_repo.create_one(update_log_repo.collection_name, {
                "competitor": "N/A",  # Eğer genel bot hatası ise
                "yacht_id": "N/A",
                "last_update_date": datetime.now(),
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now()
            })

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
                try:
                    bot_instance.tracker.driver.quit()
                except Exception as ex:
                    logger.warning(f"Error while quitting driver: {ex}")
            bot_instance.tracker = None
        else:
            bot_instance.message = "Bot is already stopped."

        return BotStatusResponse(
            bot_type=bot_type,
            status=bot_instance.status,
            message=bot_instance.message,
            last_run=bot_instance.last_run,
            next_run=bot_instance.next_run,
            bot_last_started=bot_instance.last_started,
        )

    async def get_bot_status(self, bot_type: BotType) -> BotStatusResponse:
        bot_instance = self.bots[bot_type]
        return BotStatusResponse(
            bot_type=bot_type,
            status=bot_instance.status,
            message=bot_instance.message,
            last_run=bot_instance.last_run,
            next_run=bot_instance.next_run,
            bot_last_started=bot_instance.last_started,
        )
