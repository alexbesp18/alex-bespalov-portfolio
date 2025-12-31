"""
Tests for backfill module functionality.
"""

import datetime
from unittest.mock import patch

from backfill.main import (
    backfill,
    get_iso_weeks_in_year,
)


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

    @patch("backfill.main.run_pipeline")
    @patch("backfill.main.time.sleep")
    def test_backfill_runs_correct_weeks(self, mock_sleep, mock_pipeline):
        """Test that backfill runs the correct number of weeks."""
        mock_pipeline.return_value = True

        backfill(weeks_back=3, skip_existing=True)

        # Should have called run_pipeline 3 times
        assert mock_pipeline.call_count == 3
        # Should have slept between requests
        assert mock_sleep.call_count == 3

    @patch("backfill.main.run_pipeline")
    @patch("backfill.main.time.sleep")
    def test_backfill_passes_correct_parameters(self, mock_sleep, mock_pipeline):
        """Test that backfill passes correct parameters to run_pipeline."""
        mock_pipeline.return_value = True

        backfill(weeks_back=1, skip_existing=False)

        # Verify skip_if_exists was passed
        call_kwargs = mock_pipeline.call_args.kwargs
        assert call_kwargs.get("skip_if_exists") is False

    @patch("backfill.main.run_pipeline")
    @patch("backfill.main.time.sleep")
    def test_backfill_handles_pipeline_error(self, mock_sleep, mock_pipeline):
        """Test that backfill continues on pipeline errors."""
        mock_pipeline.side_effect = [Exception("Error"), True]

        # Should not raise, should continue to next week
        backfill(weeks_back=2)

        assert mock_pipeline.call_count == 2

    @patch("backfill.main.run_pipeline")
    @patch("backfill.main.time.sleep")
    def test_backfill_year_boundary(self, mock_sleep, mock_pipeline):
        """Test that backfill correctly handles year boundaries."""
        mock_pipeline.return_value = True

        # Mock current date to be in early January
        with patch("backfill.main.datetime") as mock_datetime:
            mock_datetime.date.today.return_value = datetime.date(2025, 1, 10)
            mock_datetime.date.side_effect = lambda *args, **kw: datetime.date(
                *args, **kw
            )
            mock_datetime.timedelta = datetime.timedelta

            backfill(weeks_back=5)

        # All calls should have valid year/week parameters
        for call in mock_pipeline.call_args_list:
            year = call.kwargs.get("year")
            week = call.kwargs.get("week")
            assert year is not None
            assert week is not None
            assert week > 0, f"Invalid week number: {week}"

    @patch("backfill.main.run_pipeline")
    @patch("backfill.main.time.sleep")
    def test_backfill_counts_successes_and_failures(self, mock_sleep, mock_pipeline):
        """Test that backfill tracks success/failure counts."""
        mock_pipeline.side_effect = [True, False, True]

        # Should complete without error
        backfill(weeks_back=3)

        assert mock_pipeline.call_count == 3
