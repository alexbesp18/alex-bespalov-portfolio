"""
Tests for backfill module functionality.
"""
import datetime
from unittest.mock import patch, MagicMock

import pytest

from backfill.main import (
    get_week_url,
    get_week_start_date,
    get_iso_weeks_in_year,
    backfill,
)


class TestGetWeekUrl:
    """Tests for URL construction."""

    def test_basic_url(self):
        """Test URL format is correct."""
        url = get_week_url(2025, 10)
        assert url == "https://www.producthunt.com/leaderboard/weekly/2025/10"

    def test_single_digit_week(self):
        """Test URL with single digit week."""
        url = get_week_url(2025, 1)
        assert url == "https://www.producthunt.com/leaderboard/weekly/2025/1"


class TestGetWeekStartDate:
    """Tests for week start date calculation."""

    def test_known_week(self):
        """Test a known week returns correct Monday."""
        # Week 1 of 2025 starts on Dec 30, 2024 (Monday)
        result = get_week_start_date(2025, 1)
        assert result == "2024-12-30"

    def test_mid_year_week(self):
        """Test a mid-year week."""
        # Week 26 of 2025
        result = get_week_start_date(2025, 26)
        # Should be a Monday in late June
        parsed = datetime.datetime.strptime(result, "%Y-%m-%d")
        assert parsed.weekday() == 0  # Monday


class TestGetIsoWeeksInYear:
    """Tests for ISO week count calculation."""

    def test_52_week_year(self):
        """Test a year with 52 weeks."""
        # 2025 has 52 weeks
        assert get_iso_weeks_in_year(2025) == 52

    def test_53_week_year(self):
        """Test a year with 53 weeks."""
        # 2020 had 53 weeks
        assert get_iso_weeks_in_year(2020) == 53

    def test_another_53_week_year(self):
        """Test another year with 53 weeks."""
        # 2026 has 53 weeks
        assert get_iso_weeks_in_year(2026) == 53


class TestBackfill:
    """Tests for the backfill function."""

    @patch('backfill.main.save_to_gsheet')
    @patch('backfill.main.parse_products')
    @patch('backfill.main.fetch_html')
    @patch('backfill.main.time.sleep')
    def test_backfill_fetches_correct_weeks(
        self, mock_sleep, mock_fetch, mock_parse, mock_save
    ):
        """Test that backfill fetches the correct number of weeks."""
        mock_fetch.return_value = "<html></html>"
        mock_parse.return_value = []

        backfill(weeks_back=3)

        # Should have fetched 3 weeks
        assert mock_fetch.call_count == 3
        # Should have slept between requests
        assert mock_sleep.call_count == 3

    @patch('backfill.main.save_to_gsheet')
    @patch('backfill.main.parse_products')
    @patch('backfill.main.fetch_html')
    @patch('backfill.main.time.sleep')
    def test_backfill_saves_products(
        self, mock_sleep, mock_fetch, mock_parse, mock_save
    ):
        """Test that backfill saves products when found."""
        mock_fetch.return_value = "<html></html>"
        mock_product = MagicMock()
        mock_parse.return_value = [mock_product]

        backfill(weeks_back=1)

        mock_save.assert_called_once()
        # Verify date_override was passed
        call_args = mock_save.call_args
        assert 'date_override' in call_args.kwargs

    @patch('backfill.main.save_to_gsheet')
    @patch('backfill.main.parse_products')
    @patch('backfill.main.fetch_html')
    @patch('backfill.main.time.sleep')
    def test_backfill_handles_fetch_error(
        self, mock_sleep, mock_fetch, mock_parse, mock_save
    ):
        """Test that backfill continues on fetch errors."""
        mock_fetch.side_effect = [Exception("Network error"), "<html></html>"]
        mock_parse.return_value = []

        # Should not raise, should continue to next week
        backfill(weeks_back=2)

        assert mock_fetch.call_count == 2

    @patch('backfill.main.save_to_gsheet')
    @patch('backfill.main.parse_products')
    @patch('backfill.main.fetch_html')
    @patch('backfill.main.time.sleep')
    def test_backfill_year_boundary(
        self, mock_sleep, mock_fetch, mock_parse, mock_save
    ):
        """Test that backfill correctly handles year boundaries."""
        mock_fetch.return_value = "<html></html>"
        mock_parse.return_value = []

        # Mock current date to be in early January
        with patch('backfill.main.datetime') as mock_datetime:
            mock_datetime.date.today.return_value = datetime.date(2025, 1, 10)
            mock_datetime.date.side_effect = lambda *args, **kw: datetime.date(*args, **kw)
            mock_datetime.timedelta = datetime.timedelta

            backfill(weeks_back=5)

        # All calls should have valid URLs (no negative weeks)
        for call in mock_fetch.call_args_list:
            url = call[0][0]
            # Extract week number from URL
            week_num = int(url.split('/')[-1])
            assert week_num > 0, f"Invalid week number in URL: {url}"
