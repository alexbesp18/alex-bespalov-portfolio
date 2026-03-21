"""
Unit tests for merchant name normalization and fuzzy matching.
"""

import pytest
from core.normalizer import (
    normalize_merchant,
    find_best_match,
    find_all_matches,
    match_merchants,
    get_canonical_name,
    extract_merchant_keywords,
)


class TestNormalizeMerchant:
    """Tests for normalize_merchant function."""

    def test_basic_normalization(self):
        """Test basic lowercase and strip."""
        assert normalize_merchant("  Amazon  ") == "amazon"
        assert normalize_merchant("WALMART") == "walmart"

    def test_removes_common_suffixes(self):
        """Test removal of .com, .net, Inc, LLC, etc."""
        assert normalize_merchant("Amazon.com") == "amazon"
        assert normalize_merchant("Target.com") == "target"
        assert normalize_merchant("Apple Inc") == "apple"
        assert normalize_merchant("Microsoft Corp.") == "microsoft"
        assert normalize_merchant("Acme LLC") == "acme"

    def test_removes_special_characters(self):
        """Test removal of special characters."""
        # Apostrophes are kept for readability
        assert normalize_merchant("Macy's") == "macy's"
        assert normalize_merchant("AT&T") == "att"
        assert normalize_merchant("B&H Photo") == "bh photo"

    def test_normalizes_hyphens_and_spaces(self):
        """Test hyphen and space normalization."""
        # Hyphens converted to spaces, then alias resolution applied
        assert normalize_merchant("1-800-Flowers") == "1-800-flowers"
        assert normalize_merchant("Door-Dash") == "doordash"  # alias resolved
        assert normalize_merchant("Uber   Eats") == "ubereats"  # alias resolved

    def test_handles_empty_and_none(self):
        """Test edge cases with empty/None input."""
        assert normalize_merchant("") == ""
        assert normalize_merchant("   ") == ""

    def test_known_aliases(self):
        """Test that known aliases are resolved."""
        # These depend on config.settings.matching.aliases
        assert normalize_merchant("Kindle and Kindle Unlimited") == "amazon kindle"
        assert normalize_merchant("amazoncom") == "amazon"
        assert normalize_merchant("uber eats") == "ubereats"

    def test_complex_names(self):
        """Test complex merchant names."""
        assert normalize_merchant("The Home Depot, Inc.") == "the home depot"
        # .com suffix is removed, trailing text collapsed
        result = normalize_merchant("ASOS.com US")
        assert "asos" in result  # Contains asos
        assert normalize_merchant("Bed Bath & Beyond Online Store") == "bed bath beyond"


class TestFindBestMatch:
    """Tests for find_best_match function."""

    def test_exact_match(self):
        """Test exact matches return 100 score."""
        candidates = ["amazon", "walmart", "target"]
        result = find_best_match("amazon", candidates)
        assert result is not None
        assert result[0] == "amazon"
        assert result[1] == 100

    def test_close_match(self):
        """Test close matches are found."""
        candidates = ["amazon", "walmart", "target"]
        result = find_best_match("amazn", candidates, threshold=80)
        assert result is not None
        assert result[0] == "amazon"
        assert result[1] >= 80

    def test_no_match_below_threshold(self):
        """Test no match when below threshold."""
        candidates = ["amazon", "walmart", "target"]
        result = find_best_match("xyz corp", candidates, threshold=85)
        assert result is None

    def test_word_order_invariant(self):
        """Test that word order doesn't matter (token_sort_ratio)."""
        candidates = ["home depot", "lowes", "menards"]
        result = find_best_match("depot home", candidates, threshold=85)
        assert result is not None
        assert result[0] == "home depot"

    def test_empty_inputs(self):
        """Test with empty inputs."""
        assert find_best_match("", ["a", "b"]) is None
        assert find_best_match("test", []) is None


class TestFindAllMatches:
    """Tests for find_all_matches function."""

    def test_returns_multiple_matches(self):
        """Test returning multiple matches."""
        candidates = ["amazon", "amazon prime", "amazon kindle", "walmart"]
        results = find_all_matches("amazon", candidates, threshold=60, limit=5)
        assert len(results) >= 2
        # First result should be exact match
        assert results[0][0] == "amazon"
        assert results[0][1] == 100

    def test_respects_limit(self):
        """Test limit parameter."""
        candidates = ["a1", "a2", "a3", "a4", "a5"]
        results = find_all_matches("a", candidates, threshold=50, limit=3)
        assert len(results) <= 3


class TestMatchMerchants:
    """Tests for match_merchants function."""

    def test_matches_lists(self):
        """Test matching two merchant lists."""
        simplymiles = ["amazon", "target", "unknown store"]
        portal = ["amazon", "target", "walmart", "costco"]

        matches = match_merchants(simplymiles, portal, threshold=85)

        assert "amazon" in matches
        assert "target" in matches
        assert matches["amazon"][0] == "amazon"
        assert matches["target"][0] == "target"

    def test_fuzzy_matches(self):
        """Test fuzzy matching between lists."""
        simplymiles = ["amazon kindle", "the home depot"]
        portal = ["kindle", "home depot"]

        matches = match_merchants(simplymiles, portal, threshold=70)

        # Should find partial matches
        assert len(matches) >= 1


class TestGetCanonicalName:
    """Tests for get_canonical_name function."""

    def test_returns_alias(self):
        """Test that aliases are returned."""
        assert get_canonical_name("Uber Eats") == "ubereats"
        assert get_canonical_name("Door Dash") == "doordash"

    def test_returns_normalized_if_no_alias(self):
        """Test normalized name when no alias exists."""
        assert get_canonical_name("Some Random Store.com") == "some random"


class TestExtractMerchantKeywords:
    """Tests for extract_merchant_keywords function."""

    def test_extracts_meaningful_words(self):
        """Test keyword extraction."""
        keywords = extract_merchant_keywords("The Home Depot Store")
        assert "home" in keywords
        assert "depot" in keywords
        assert "the" not in keywords
        assert "store" not in keywords

    def test_filters_short_words(self):
        """Test that short words are filtered."""
        keywords = extract_merchant_keywords("A B C Big Company")
        # "company" is filtered as it's in stopwords (common suffix)
        assert "big" in keywords
        # Single letters are filtered out (< 3 chars)
        assert len([k for k in keywords if len(k) <= 2]) == 0

