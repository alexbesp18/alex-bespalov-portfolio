"""Fetcher tests."""

import pandas as pd

from fetcher import fetch_strikes_from_chain


class TestFetchStrikesFromChain:
    def test_filters_to_specific_strikes(self):
        df = pd.DataFrame({
            "strike": [100, 150, 200, 250, 300],
            "bid": [50, 30, 15, 5, 1],
            "ask": [52, 32, 17, 7, 3],
        })
        result = fetch_strikes_from_chain(df, {200, 300})
        assert len(result) == 2
        assert set(result["strike"]) == {200, 300}

    def test_missing_strike_returns_empty(self):
        df = pd.DataFrame({"strike": [100, 200], "bid": [10, 5], "ask": [12, 7]})
        result = fetch_strikes_from_chain(df, {999})
        assert len(result) == 0
