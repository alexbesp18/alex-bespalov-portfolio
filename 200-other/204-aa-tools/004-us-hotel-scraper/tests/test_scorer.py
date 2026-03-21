"""Tests for scoring module."""

import pytest


def test_calculate_deal_score():
    """Test deal score calculation."""
    from core.scorer import calculate_deal_score

    # High yield, low cost, 5-star should get boosted
    score1 = calculate_deal_score(yield_ratio=25.0, total_cost=80, stars=5)

    # Same yield, high cost, 2-star should be lower
    score2 = calculate_deal_score(yield_ratio=25.0, total_cost=600, stars=2)

    assert score1 > score2  # 5-star + low cost beats 2-star + high cost


def test_is_exceptional():
    """Test exceptional threshold detection."""
    from core.scorer import is_exceptional

    # 5-star at 25 LP/$ is exceptional (threshold: 20)
    assert is_exceptional(25.0, 5) is True

    # 2-star at 30 LP/$ is NOT exceptional (threshold: 40)
    assert is_exceptional(30.0, 2) is False

    # 2-star at 45 LP/$ IS exceptional
    assert is_exceptional(45.0, 2) is True


def test_star_display():
    """Test star rating display."""
    from core.scorer import format_star_display

    assert format_star_display(5) == "★★★★★"
    assert format_star_display(3) == "★★★☆☆"
    assert format_star_display(0) == "Unrated"
