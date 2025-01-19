from datetime import datetime, timedelta
from src.core.tracker.nausys_tracker import NausysTracker
from src.core.tracker.mmk_tracker import MMKTracker
from src.infra.adapter.nausys_repository import NausysRepository
from src.api.dto.bot_dto import BotStatus, BotType, BotStatusResponse
from src.infra.adapter.entity.nausys_entity import NausysCompanyData, NausysYachtData, NausysPeriod, NausysYachtDetail, NausysPrice
import logging
import asyncio
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class BotController:
    _instance = None
    _bot_status: Dict[BotType, BotStatus] = {
        BotType.NAUSYS: BotStatus.STOPPED,
        BotType.MMK: BotStatus.STOPPED
    }
    _last_run: Dict[BotType, Optional[datetime]] = {
        BotType.NAUSYS: None,
        BotType.MMK: None
    }
    _next_run: Dict[BotType, Optional[datetime]] = {
        BotType.NAUSYS: None,
        BotType.MMK: None
    }
    _tasks: Dict[BotType, Optional[asyncio.Task]] = {
        BotType.NAUSYS: None,
        BotType.MMK: None
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BotController, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        self.nausys_repo = NausysRepository()

    async def start_bot(self, bot_type: BotType, interval_minutes: int = 60) -> BotStatusResponse:
        """Start a specific bot with given interval"""
        if self._bot_status[bot_type] == BotStatus.RUNNING:
            return BotStatusResponse(
                bot_type=bot_type,
                status=BotStatus.RUNNING,
                message=f"{bot_type.value} bot is already running",
                last_run=self._last_run[bot_type],
                next_run=self._next_run[bot_type]
            )

        # Create and start the background task
        self._tasks[bot_type] = asyncio.create_task(
            self._run_bot_periodically(bot_type, interval_minutes)
        )

        self._bot_status[bot_type] = BotStatus.RUNNING
        self._next_run[bot_type] = datetime.utcnow() + timedelta(minutes=interval_minutes)

        return BotStatusResponse(
            bot_type=bot_type,
            status=BotStatus.RUNNING,
            message=f"{bot_type.value} bot started successfully",
            last_run=self._last_run[bot_type],
            next_run=self._next_run[bot_type]
        )

    async def stop_bot(self, bot_type: BotType) -> BotStatusResponse:
        """Stop a specific bot"""
        if self._bot_status[bot_type] != BotStatus.RUNNING:
            return BotStatusResponse(
                bot_type=bot_type,
                status=self._bot_status[bot_type],
                message=f"{bot_type.value} bot is not running",
                last_run=self._last_run[bot_type],
                next_run=None
            )

        if self._tasks[bot_type]:
            self._tasks[bot_type].cancel()
            self._tasks[bot_type] = None

        self._bot_status[bot_type] = BotStatus.STOPPED
        self._next_run[bot_type] = None

        return BotStatusResponse(
            bot_type=bot_type,
            status=BotStatus.STOPPED,
            message=f"{bot_type.value} bot stopped successfully",
            last_run=self._last_run[bot_type],
            next_run=None
        )

    async def get_bot_status(self, bot_type: BotType) -> BotStatusResponse:
        """Get current status of a specific bot"""
        return BotStatusResponse(
            bot_type=bot_type,
            status=self._bot_status[bot_type],
            message=f"Current status of {bot_type.value} bot",
            last_run=self._last_run[bot_type],
            next_run=self._next_run[bot_type]
        )

    async def _run_bot_periodically(self, bot_type: BotType, interval_minutes: int):
        """Run the specified bot periodically"""
        while True:
            try:
                if bot_type == BotType.NAUSYS:
                    await self._run_nausys_bot()
                else:
                    await self._run_mmk_bot()

                self._last_run[bot_type] = datetime.utcnow()
                self._next_run[bot_type] = datetime.utcnow() + timedelta(minutes=interval_minutes)
                
                await asyncio.sleep(interval_minutes * 60)  # Convert minutes to seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in {bot_type.value} bot: {str(e)}")
                self._bot_status[bot_type] = BotStatus.ERROR
                break

    async def _run_nausys_bot(self):
        """Run the Nausys bot to collect data"""
        tracker = None
        try:
            tracker = NausysTracker()
            tracker.setup_driver()
            
            if not tracker.login():
                raise Exception("Failed to login to Nausys")

            results = tracker.process_all_yachts()
            if results:
                for company_id, yacht_data in results.items():
                    yacht_list = []
                    for yacht_id, periods in yacht_data.items():
                        period_list = []
                        for period_data in periods:
                            yacht_details = []
                            for detail in period_data["details"]:
                                price = NausysPrice(
                                    discounted_price=detail["prices"]["discounted_price"],
                                    original_price=detail["prices"]["original_price"],
                                    discount_percentage=detail["prices"]["discount_percentage"]
                                )
                                yacht_detail = NausysYachtDetail(
                                    yacht_name=detail["yacht_name"],
                                    status=detail["status"],
                                    location=detail["location"],
                                    prices=price
                                )
                                yacht_details.append(yacht_detail)

                            period = NausysPeriod(
                                period_from=datetime.strptime(period_data["period_from"], "%Y-%m-%d %H:%M:%S"),
                                period_to=datetime.strptime(period_data["period_to"], "%Y-%m-%d %H:%M:%S"),
                                details=yacht_details
                            )
                            period_list.append(period)

                        yacht = NausysYachtData(
                            yacht_id=yacht_id,
                            periods=period_list
                        )
                        yacht_list.append(yacht)

                    company_data = NausysCompanyData(
                        company_id=company_id,
                        company_name=company_id,  # You might want to get actual company name from somewhere
                        yachts=yacht_list
                    )

                    # Save to database
                    success = await self.nausys_repo.save_company_data(company_data)
                    if not success:
                        logger.error(f"Failed to save data for company {company_id}")

            logger.info("Successfully updated Nausys data")
            
        except Exception as e:
            logger.error(f"Error running Nausys bot: {str(e)}")
            raise e
            
        finally:
            if tracker and tracker.driver:
                tracker.driver.quit()

    async def _run_mmk_bot(self):
        """Run the MMK bot to collect data"""
        tracker = None
        try:
            tracker = MMKTracker()
            tracker.setup_driver()
            
            if not tracker.login():
                raise Exception("Failed to login to MMK")
            
            # TODO: Implement MMK specific logic similar to Nausys
            logger.info("Successfully updated MMK data")
            
        except Exception as e:
            logger.error(f"Error running MMK bot: {str(e)}")
            raise e
            
        finally:
            if tracker and tracker.driver:
                tracker.driver.quit()
