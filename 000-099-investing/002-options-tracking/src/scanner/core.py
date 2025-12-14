"""Core scanner logic for monitoring stock options."""

import json
import signal
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yfinance as yf
from tenacity import retry, stop_after_attempt, wait_exponential
from yfinance.exceptions import YFRateLimitError

from src.config import settings
from src.scanner.models import ConfigEntry, Task
from src.utils.logging_setup import get_logger, setup_logging

# Initialize logging
setup_logging()
logger = get_logger()


class OptionsScanner:
    """Scanner for monitoring stock options opportunities."""

    def __init__(self) -> None:
        """Initialize the scanner."""
        self.running: bool = True
        self.task_list: List[Task] = []
        self.config_prev: Optional[float] = None
        self.config_curr: Optional[float] = None
        self.config_filename: Path = settings.get_config_path()
        self.stocks: Dict[str, yf.Ticker] = {}

        # Set up signal handler
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, sig: int, frame) -> None:
        """Handle interrupt signal.

        Args:
            sig: Signal number.
            frame: Current stack frame.
        """
        self.running = False
        logger.info("Received interrupt signal, shutting down...")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        reraise=True,
    )
    def _get_ticker(self, ticker_symbol: str) -> yf.Ticker:
        """Get yfinance Ticker object with retry logic.

        Args:
            ticker_symbol: Stock ticker symbol.

        Returns:
            yfinance Ticker object.

        Raises:
            YFRateLimitError: If rate limit is exceeded after retries.
            Exception: For other API errors.
        """
        try:
            return yf.Ticker(ticker_symbol)
        except YFRateLimitError as e:
            logger.error(f"YFinance rate limit exceeded for {ticker_symbol}")
            raise
        except Exception as e:
            logger.error(
                f"Failed to create ticker object for {ticker_symbol}: {e.__class__.__name__}"
            )
            raise

    def process_request(self, task: Task) -> bool:
        """Process a single options chain request.

        Args:
            task: Task containing ticker, date, and filter parameters.

        Returns:
            True if matching options found, False otherwise.
        """
        try:
            stock = self.stocks.get(task.ticker)
            if not stock:
                logger.warning(f"Ticker {task.ticker} not found in stocks cache")
                return False

            # Get options chain for the specified date
            try:
                chain = stock.option_chain(task.date)
            except Exception as e:
                logger.error(f"Failed to get options chain for {task.ticker} on {task.date}: {e}")
                return False

            # Select calls or puts
            if task.type == "Call":
                data = chain.calls
            elif task.type == "Put":
                data = chain.puts
            else:
                logger.warning(f"Unknown option type: {task.type}")
                return False

            if data.empty:
                return False

            # Filter for out-of-the-money options
            data = data[data["inTheMoney"] == False]  # noqa: E712

            # Check if we have any OTM options
            if data.empty:
                return False

            # Validate price is positive
            if task.price <= 0:
                logger.warning(f"Invalid price for {task.ticker}: {task.price}")
                return False

            # Calculate OTM coefficients
            otm_min_coeff = 1 + task.otm_min / 100
            otm_max_coeff = 1 + task.otm_max / 100

            # Validate coefficient ranges
            if otm_min_coeff >= otm_max_coeff:
                logger.warning(
                    f"Invalid OTM range for {task.ticker}: min={task.otm_min}%, max={task.otm_max}%"
                )
                return False

            # Filter by strike price range and open interest
            otm_strikes = data[
                (data["strike"] > (task.price * otm_min_coeff))
                & (data["strike"] < (task.price * otm_max_coeff))
                & (data["openInterest"] > task.open_interest)
            ]

            return otm_strikes.shape[0] > 0

        except Exception as e:
            logger.error(f"Error processing request for {task.ticker}: {e}", exc_info=True)
            return False

    def check_config(self) -> bool:
        """Check if configuration file has been modified.

        Returns:
            True if config file was modified, False otherwise.
        """
        try:
            if not self.config_filename.exists():
                logger.critical("Config file was deleted since last read")
                return False

            self.config_prev = self.config_curr
            self.config_curr = self.config_filename.stat().st_mtime

            if self.config_prev is not None and self.config_prev != self.config_curr:
                return True

            return False
        except (OSError, FileNotFoundError) as e:
            logger.error(f"Error checking config file: {e}")
            return False

    def date_list(self, dates: List[str], date_start: str, date_end: str) -> List[str]:
        """Filter dates within a specified range.

        Args:
            dates: List of date strings in YYYY-MM-DD format.
            date_start: Start date in YYYY-MM-DD format (inclusive).
            date_end: End date in YYYY-MM-DD format (exclusive).

        Returns:
            List of dates within the specified range.
        """
        if not dates:
            return []

        date_format = "%Y-%m-%d"
        try:
            dt_start = datetime.strptime(date_start, date_format)
            dt_end = datetime.strptime(date_end, date_format)
        except ValueError as e:
            logger.error(f"Invalid date format: {e}")
            return []

        # Validate date range
        if dt_start >= dt_end:
            logger.warning(f"Invalid date range: start={date_start}, end={date_end}")
            return []

        result = []
        for date in dates:
            try:
                dt = datetime.strptime(date, date_format)
                if dt_start <= dt < dt_end:
                    result.append(date)
            except ValueError:
                logger.warning(f"Skipping invalid date: {date}")
                continue

        return result

    def process_config(self) -> None:
        """Load and process configuration file.

        Reads JSONL config file, creates Ticker objects, and generates task list.
        """
        self.task_list = []
        self.stocks = {}

        # Read configuration file
        data_list: List[ConfigEntry] = []
        try:
            with open(self.config_filename, "r", encoding="utf-8") as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        data_dict = json.loads(line)
                        config_entry = ConfigEntry(**data_dict)
                        data_list.append(config_entry)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping malformed line {line_num}: {line.strip()}")
                        continue
                    except Exception as e:
                        logger.warning(f"Skipping invalid config entry on line {line_num}: {e}")
                        continue

        except FileNotFoundError:
            logger.critical(f"Config file not found: {self.config_filename}")
            raise
        except PermissionError:
            logger.critical(f"Permission denied reading config file: {self.config_filename}")
            raise
        except Exception as e:
            logger.critical(f"Error reading config file: {e}")
            raise

        if not data_list:
            logger.error("No valid configuration entries found in file")
            return

        # Process each configuration entry
        for data_entry in data_list:
            if not data_entry.enabled:
                continue

            ticker = data_entry.ticker

            try:
                stock = self._get_ticker(ticker)
                self.stocks[ticker] = stock
            except YFRateLimitError:
                logger.error(f"Rate limit exceeded for {ticker}, skipping")
                continue
            except Exception as e:
                logger.error(f"Failed to create ticker for {ticker}: {e}")
                continue

            # Get current price
            try:
                price = stock.info.get("currentPrice")
                if price is None:
                    logger.warning(f"Could not get current price for {ticker}")
                    continue
            except Exception as e:
                logger.error(f"Error getting price for {ticker}: {e}")
                continue

            # Get available expiration dates
            try:
                available_dates = list(stock.options)
            except Exception as e:
                logger.error(f"Error getting expiration dates for {ticker}: {e}")
                continue

            # Filter dates within range
            date_list = self.date_list(
                available_dates, data_entry.start_date, data_entry.end_date
            )

            # Create tasks for each expiration date
            for date in date_list:
                task = Task(
                    ticker=ticker,
                    date=date,
                    price=price,
                    strike=data_entry.strike,
                    type=data_entry.type,
                    otm_min=data_entry.otm_min,
                    otm_max=data_entry.otm_max,
                    open_interest=data_entry.open_interest,
                )
                self.task_list.append(task)

        logger.info(f"Loaded {len(self.stocks)} tickers")
        logger.info(f"Generated {len(self.task_list)} tasks")

    def send_notification(self, task: Task) -> None:
        """Send notification when matching options are found.

        Args:
            task: Task that matched the criteria.
        """
        logger.info(
            f"Found OTM options: {task.ticker}, {task.date}, {task.type}, "
            f"strike:{task.strike}, OI:{task.open_interest}"
        )

    def run(self) -> None:
        """Main scanner loop."""
        try:
            self.process_config()
        except Exception as e:
            logger.critical(f"Failed to process config: {e}", exc_info=True)
            return

        if not self.task_list:
            logger.warning("No tasks to process. Exiting.")
            return

        logger.info(f"Starting scanner loop with {len(self.task_list)} tasks")
        while self.running:
            try:
                # Process all tasks
                for task in self.task_list:
                    if not self.running:
                        break
                    if self.process_request(task):
                        self.send_notification(task)

                # Check for config changes
                if self.check_config():
                    logger.info("Config file changed, reloading...")
                    try:
                        self.process_config()
                    except Exception as e:
                        logger.error(f"Failed to reload config: {e}", exc_info=True)

                # Sleep to avoid CPU spinning and rate limiting
                time.sleep(settings.scanner_interval)

            except KeyboardInterrupt:
                logger.info("Exiting upon Ctrl-C")
                break
            except Exception as e:
                logger.error(f"Error in scanner loop: {e}", exc_info=True)
                # Continue running instead of breaking to allow recovery
                time.sleep(settings.scanner_interval)


def main() -> None:
    """Entry point for scanner application."""
    scanner = OptionsScanner()
    scanner.run()


if __name__ == "__main__":
    main()

