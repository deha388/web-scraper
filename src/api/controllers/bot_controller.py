import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

from src.infra.config.init_database import init_database
from src.api.dto.bot_dto import BotStatus, BotType, BotStatusResponse
from src.infra.adapter.update_log_repository import UpdateLogRepository
from src.infra.adapter.booking_data_repository import BookingDataRepository
from src.core.tracker.nausys_tracker import NausysTracker
from src.core.tracker.mmk_tracker import MMKTracker

logger = logging.getLogger(__name__)


class BotInstance:
    def __init__(self):
        self.status: BotStatus = BotStatus.STOPPED
        self.last_started: Optional[datetime] = None
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.task: Optional[asyncio.Task] = None
        self.message: str = ""
        self.tracker: Optional[MMKTracker] = None


class BotController:
    def __init__(self, db=None):
        if db is None:
            db = init_database()
        self.db = db
        self.bots: Dict[BotType, BotInstance] = {
            BotType.MMK: BotInstance()
        }

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

        try:
            bot_instance.status = BotStatus.RUNNING
            bot_instance.last_started = datetime.now()
            bot_instance.message = "Bot started. Running daily jobs."

            if bot_instance.tracker is None:
                if bot_type == BotType.NAUSYS:
                    bot_instance.tracker = NausysTracker()
                elif bot_type == BotType.MMK:
                    bot_instance.tracker = MMKTracker()

                try:
                    bot_instance.tracker.setup_driver()
                except Exception as setup_exc:
                    logger.error(f"[{bot_type}] Driver setup error: {setup_exc}", exc_info=True)
                    bot_instance.message = "Error during driver setup. Bot will retry on next scheduled run."

                try:
                    if not await bot_instance.tracker.login():
                        bot_instance.message = "Initial login failed. Bot will retry on next scheduled run."
                        logger.error(f"[{bot_type}] Initial login failed.")
                except Exception as login_exc:
                    logger.error(f"[{bot_type}] Exception during login attempt: {login_exc}", exc_info=True)
                    bot_instance.message = "Exception during login. Bot will retry on next scheduled run."

            bot_instance.task = asyncio.create_task(self._daily_scheduler(bot_type))
            await self._run_daily_job(bot_type)
        except Exception as e:
            logger.error(f"[{bot_type}] Exception during starting bot: {e}", exc_info=True)
            bot_instance.status = BotStatus.STOPPED
            bot_instance.message = f"Failed to start bot: {str(e)}"
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
            next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            bot_instance.next_run = next_midnight
            seconds_to_wait = (next_midnight - now).total_seconds()
            logger.info(f"[{bot_type}] Sleeping until {next_midnight} (~{int(seconds_to_wait)}s).")
            try:
                await asyncio.sleep(seconds_to_wait)
            except asyncio.CancelledError:
                logger.info(f"[{bot_type}] Daily scheduler cancelled.")
                break
            except Exception as e:
                logger.error(f"[{bot_type}] Error in daily scheduler: {e}", exc_info=True)
                break

            if bot_instance.status == BotStatus.RUNNING:
                await self._run_daily_job(bot_type)

    async def _run_daily_job(self, bot_type: BotType):
        bot_instance = self.bots[bot_type]
        if bot_instance.tracker is None:
            logger.error(f"[{bot_type}] Tracker instance not found; daily job skipped.")
            return

        if not bot_instance.tracker.logged_in:
            logger.info(f"[{bot_type}] Session appears to be expired; attempting re-login...")
            try:
                if not await bot_instance.tracker.login():
                    bot_instance.message = "Login failed during daily run. Will retry at next scheduled time."
                    logger.error(f"[{bot_type}] Login failed during daily run.")
                    return
            except Exception as e:
                bot_instance.message = f"Exception during re-login: {str(e)}. Will retry at next scheduled time."
                logger.error(f"[{bot_type}] Exception during re-login: {e}", exc_info=True)
                return

        try:
            db_client = self.db.db_session
            database = db_client["boat_tracker"]
            book_repo = BookingDataRepository(database, "booking_data_mmk")
            update_log_repo = UpdateLogRepository(database)
            await bot_instance.tracker.fetch_competitor_weekly_price_quotes(book_repo=book_repo, update_log_repo=update_log_repo)
            bot_instance.last_run = datetime.now()
            bot_instance.message = f"Daily run completed successfully at {bot_instance.last_run}."
            logger.info(f"[{bot_type}] Daily run completed at {bot_instance.last_run}.")
        except Exception as e:
            bot_instance.message = f"Error during daily job: {str(e)}. Will retry at next scheduled time."
            logger.error(f"[{bot_type}] Error during daily job: {e}", exc_info=True)

            try:
                db_client = self.db.db_session
                database = db_client["boat_tracker"]
                update_log_repo = UpdateLogRepository(database)
                await update_log_repo.create_one(update_log_repo.collection_name, {
                    "competitor": "N/A",
                    "yacht_id": "N/A",
                    "last_update_date": datetime.now(),
                    "status": "error",
                    "error": str(e),
                    "timestamp": datetime.now()
                })
            except Exception as log_exc:
                logger.error(f"[{bot_type}] Failed to log error to database: {log_exc}", exc_info=True)

    async def stop_bot(self, bot_type: BotType) -> BotStatusResponse:
        bot_instance = self.bots[bot_type]
        try:
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
                        logger.warning(f"[{bot_type}] Error while quitting driver: {ex}", exc_info=True)
                bot_instance.tracker = None
            else:
                bot_instance.message = "Bot is already stopped."
        except Exception as e:
            logger.error(f"[{bot_type}] Exception during stopping bot: {e}", exc_info=True)
            bot_instance.message = f"Error while stopping bot: {str(e)}"
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
