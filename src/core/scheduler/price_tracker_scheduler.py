from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from src.core.tracker.nausys_tracker import NausysTracker
from src.core.tracker.mmk_tracker import MMKTracker
from src.infra.config.database import Price
from src.infra.config.database import get_database
import logging

logger = logging.getLogger(__name__)


class PriceTrackerScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.db = get_database()

    def start(self):
        """Start the scheduler to run price tracking hourly"""
        self.scheduler.add_job(
            self.track_prices,
            'interval',
            hours=1,
            next_run_time=datetime.now()  # Run immediately when started
        )
        self.scheduler.start()
        logger.info("Price tracker scheduler started")

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Price tracker scheduler stopped")

    async def track_prices(self):
        """Run price tracking for all competitors"""
        try:
            # Get active competitors
            competitors = await self.db.competitors.find({"is_active": True}).to_list(None)

            # Track Nausys prices
            nausys_competitors = [c for c in competitors if c["platform"] == "nausys"]
            if nausys_competitors:
                await self._track_nausys_prices(nausys_competitors)

            # Track MMK prices
            mmk_competitors = [c for c in competitors if c["platform"] == "mmk"]
            if mmk_competitors:
                await self._track_mmk_prices(mmk_competitors)

        except Exception as e:
            logger.error(f"Error in price tracking: {str(e)}")

    async def _track_nausys_prices(self, competitors):
        """Track prices from Nausys platform"""
        try:
            tracker = NausysTracker()
            tracker.setup_driver()
            if not tracker.login():
                logger.error("Failed to login to Nausys")
                return

            for competitor in competitors:
                try:
                    # Process each yacht
                    results = tracker.process_all_yachts()

                    # Parse and store results
                    if results:
                        for company, yacht_data in results.items():
                            for yacht_id, periods in yacht_data.items():
                                for period in periods:
                                    for detail in period["details"]:
                                        # Create price record
                                        price_record = Price(
                                            platform="nausys",
                                            competitor_id=competitor["_id"],
                                            boat_id=yacht_id,
                                            week_start=datetime.strptime(period["period_from"], "%Y-%m-%d %H:%M:%S"),
                                            week_end=datetime.strptime(period["period_to"], "%Y-%m-%d %H:%M:%S"),
                                            price=float(detail["prices"]["discounted_price"].split()[0].replace(".",
                                                                                                                "").replace(
                                                ",", ".")),
                                            our_price=0.0,  # This should be fetched from your own pricing system
                                            price_diff=0.0,  # Will be calculated after getting our_price
                                            status="normal"  # Will be determined based on price_diff
                                        )

                                        # Store in MongoDB
                                        await self.db.prices.insert_one(price_record.dict())

                except Exception as e:
                    logger.error(f"Error processing competitor {competitor['name']}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error in Nausys tracking: {str(e)}")
        finally:
            if tracker and tracker.driver:
                tracker.driver.quit()

    async def _track_mmk_prices(self, competitors):
        """Track prices from MMK platform"""
        try:
            tracker = MMKTracker()
            tracker.setup_driver()
            if not tracker.login():
                logger.error("Failed to login to MMK")
                return

            # Similar implementation as Nausys tracking
            # This needs to be implemented based on MMK's specific data structure
            pass

        except Exception as e:
            logger.error(f"Error in MMK tracking: {str(e)}")
        finally:
            if tracker:
                tracker.cleanup()
