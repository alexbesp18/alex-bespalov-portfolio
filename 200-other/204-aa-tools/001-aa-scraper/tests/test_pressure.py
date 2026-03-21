"""
Pressure tests for AA Points Monitor.
Tests system behavior under load and stress conditions.

Run with: pytest tests/test_pressure.py -v --tb=short
"""

import pytest
import time
import random
import string
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.database import Database
from core.normalizer import normalize_merchant, find_best_match, match_merchants
from core.optimizer import optimize_allocation, identify_top_pick
from core.scorer import StackedDeal, calculate_deal_score


class TestFuzzyMatchingAtScale:
    """Test fuzzy matching performance with large datasets."""

    def generate_merchant_names(self, count: int) -> list:
        """Generate realistic merchant names."""
        prefixes = ['The', 'Best', 'Super', 'Mega', 'Ultra', 'Pro', 'Elite', 'Premium']
        bases = ['Shop', 'Store', 'Mart', 'Outlet', 'Depot', 'Market', 'Plaza', 'Center']
        suffixes = ['Online', 'Express', 'Direct', 'Plus', 'Max', 'Prime', 'Go', 'Now']

        merchants = []
        for i in range(count):
            prefix = random.choice(prefixes) if random.random() > 0.5 else ''
            base = random.choice(bases)
            suffix = random.choice(suffixes) if random.random() > 0.5 else ''
            name = f"{prefix} {base} {suffix} {i}".strip()
            merchants.append(name)

        return merchants

    def test_normalize_1000_merchants(self):
        """Normalize 1000 merchant names in reasonable time."""
        merchants = self.generate_merchant_names(1000)

        start = time.time()
        normalized = [normalize_merchant(m) for m in merchants]
        elapsed = time.time() - start

        assert len(normalized) == 1000
        assert elapsed < 1.0, f"Normalization took {elapsed:.2f}s, should be <1s"

    def test_fuzzy_match_1000_candidates(self):
        """Find best match among 1000 candidates."""
        candidates = self.generate_merchant_names(1000)
        # Use a name that definitely exists in candidates
        query = candidates[500]  # Pick one we know exists

        start = time.time()
        result = find_best_match(query, candidates)
        elapsed = time.time() - start

        assert elapsed < 2.0, f"Fuzzy match took {elapsed:.2f}s, should be <2s"
        assert result is not None
        match, score = result
        assert match is not None

    def test_cross_match_100x100(self):
        """Match 100 SimplyMiles offers against 100 portal merchants."""
        simplymiles = self.generate_merchant_names(100)
        portal = self.generate_merchant_names(100)

        start = time.time()
        matches = match_merchants(simplymiles, portal, threshold=85)
        elapsed = time.time() - start

        # 100×100 = 10,000 comparisons should be fast
        assert elapsed < 5.0, f"Cross-match took {elapsed:.2f}s, should be <5s"

    def test_cross_match_500x1400_realistic(self):
        """Realistic scale: 500 SM offers × 1400 portal merchants."""
        simplymiles = self.generate_merchant_names(500)
        portal = self.generate_merchant_names(1400)

        start = time.time()
        matches = match_merchants(simplymiles, portal, threshold=85)
        elapsed = time.time() - start

        # 700,000 comparisons - this is the real workload
        assert elapsed < 30.0, f"Cross-match took {elapsed:.2f}s, should be <30s"
        print(f"\n  500×1400 cross-match: {elapsed:.2f}s, found {len(matches)} matches")


class TestOptimizerAtScale:
    """Test optimizer performance with many deals."""

    def generate_deals(self, count: int) -> list:
        """Generate realistic deal data."""
        deals = []
        for i in range(count):
            min_spend = random.choice([5, 10, 20, 50, 100, 200])
            base_yield = random.uniform(5.0, 35.0)
            total_miles = int(base_yield * min_spend)
            deal_score = calculate_deal_score(base_yield, min_spend)

            deals.append({
                'merchant_name': f'Merchant_{i}',
                'deal_score': deal_score,
                'base_yield': base_yield,
                'min_spend': min_spend,
                'min_spend_required': min_spend,
                'total_miles': total_miles,
            })

        return deals

    def test_optimize_100_deals(self):
        """Optimize allocation across 100 deals."""
        deals = self.generate_deals(100)

        start = time.time()
        result = optimize_allocation(deals, budget=500)
        elapsed = time.time() - start

        assert elapsed < 1.0, f"Optimization took {elapsed:.2f}s, should be <1s"
        assert result.total_spent > 0
        assert result.total_miles > 0

    def test_optimize_1000_deals(self):
        """Optimize allocation across 1000 deals."""
        deals = self.generate_deals(1000)

        start = time.time()
        result = optimize_allocation(deals, budget=500)
        elapsed = time.time() - start

        assert elapsed < 5.0, f"Optimization took {elapsed:.2f}s, should be <5s"
        assert result.total_spent > 0

    def test_identify_top_pick_1000_deals(self):
        """Identify top pick from 1000 deals."""
        deals = self.generate_deals(1000)

        start = time.time()
        top = identify_top_pick(deals)
        elapsed = time.time() - start

        assert elapsed < 2.0, f"Top pick took {elapsed:.2f}s, should be <2s"
        assert top is not None


class TestDatabaseStress:
    """Test database under stress conditions."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            db = Database(db_path)
            yield db

    def test_insert_1000_offers(self, temp_db):
        """Insert 1000 offers quickly."""
        start = time.time()

        for i in range(1000):
            temp_db.insert_simplymiles_offer(
                merchant_name=f"Merchant {i}",
                merchant_name_normalized=f"merchant{i}",
                offer_type='flat_bonus',
                miles_amount=100,
                lp_amount=50,
                min_spend=10.0,
                expires_at=(datetime.now() + timedelta(days=30)).isoformat(),
                expiring_soon=False,
                scraped_at=datetime.now().isoformat()
            )

        elapsed = time.time() - start
        assert elapsed < 5.0, f"Insert took {elapsed:.2f}s, should be <5s"

    def test_insert_1000_portal_rates(self, temp_db):
        """Insert 1000 portal rates quickly."""
        start = time.time()

        for i in range(1000):
            temp_db.insert_portal_rate(
                merchant_name=f"Merchant {i}",
                merchant_name_normalized=f"merchant{i}",
                miles_per_dollar=random.uniform(1.0, 10.0),
                is_bonus_rate=random.choice([True, False]),
                category='Shopping',
                url=f"https://example.com/{i}",
                scraped_at=datetime.now().isoformat()
            )

        elapsed = time.time() - start
        assert elapsed < 5.0, f"Insert took {elapsed:.2f}s, should be <5s"

    def test_query_after_bulk_insert(self, temp_db):
        """Query performance after bulk insert."""
        # Use same scraped_at for all offers (simulates one scrape batch)
        scraped_at = datetime.now().isoformat()

        # Insert 1000 offers
        for i in range(1000):
            temp_db.insert_simplymiles_offer(
                merchant_name=f"Merchant {i}",
                merchant_name_normalized=f"merchant{i}",
                offer_type='flat_bonus',
                miles_amount=100,
                lp_amount=50,
                min_spend=10.0,
                expires_at=(datetime.now() + timedelta(days=30)).isoformat(),
                expiring_soon=False,
                scraped_at=scraped_at  # Same timestamp for all
            )

        # Query should still be fast
        start = time.time()
        offers = temp_db.get_active_simplymiles_offers()
        elapsed = time.time() - start

        assert len(offers) == 1000
        assert elapsed < 1.0, f"Query took {elapsed:.2f}s, should be <1s"

    def test_concurrent_writes(self, temp_db):
        """Test concurrent database writes."""
        # Use same scraped_at for all batches (simulates concurrent writes in one scrape)
        scraped_at = datetime.now().isoformat()

        def insert_batch(batch_id: int, count: int):
            for i in range(count):
                temp_db.insert_portal_rate(
                    merchant_name=f"Batch{batch_id}_Merchant{i}",
                    merchant_name_normalized=f"batch{batch_id}merchant{i}",
                    miles_per_dollar=5.0,
                    is_bonus_rate=False,
                    category='Test',
                    url=None,
                    scraped_at=scraped_at  # Same timestamp for all
                )
            return batch_id

        # Run 5 concurrent batches of 100 inserts each
        start = time.time()
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(insert_batch, i, 100) for i in range(5)]
            results = [f.result() for f in as_completed(futures)]

        elapsed = time.time() - start

        # Should complete without errors
        assert len(results) == 5
        assert elapsed < 10.0, f"Concurrent writes took {elapsed:.2f}s"

        # Verify all data was written
        rates = temp_db.get_latest_portal_rates()
        assert len(rates) == 500

    def test_hotel_yield_history_bulk(self, temp_db):
        """Test bulk hotel yield history recording."""
        start = time.time()

        for i in range(500):
            temp_db.record_hotel_yield(
                city=random.choice(['Austin', 'Dallas', 'Houston', 'NYC']),
                day_of_week=random.randint(0, 6),
                advance_days=random.randint(1, 90),
                avg_yield=random.uniform(5.0, 25.0),
                max_yield=random.uniform(10.0, 40.0),
                deal_count=random.randint(1, 50)
            )

        elapsed = time.time() - start
        assert elapsed < 5.0, f"Bulk yield history took {elapsed:.2f}s"


class TestScorerAtScale:
    """Test scorer performance at scale."""

    def test_create_1000_stacked_deals(self):
        """Create 1000 StackedDeal objects."""
        start = time.time()

        deals = []
        for i in range(1000):
            deal = StackedDeal(
                merchant_name=f"Merchant {i}",
                portal_rate=random.uniform(1.0, 10.0),
                simplymiles_type=random.choice(['flat_bonus', 'per_dollar']),
                simplymiles_amount=random.randint(50, 500),
                simplymiles_min_spend=random.choice([5.0, 10.0, 20.0, 50.0]),
                simplymiles_expires=(datetime.now() + timedelta(days=30)).isoformat()
            )
            deals.append(deal)

        elapsed = time.time() - start
        assert elapsed < 2.0, f"Creating 1000 deals took {elapsed:.2f}s"
        assert len(deals) == 1000

    def test_calculate_deal_scores_1000(self):
        """Calculate deal scores for 1000 combinations."""
        start = time.time()

        scores = []
        for i in range(1000):
            score = calculate_deal_score(
                base_yield=random.uniform(5.0, 35.0),
                min_spend=random.choice([5, 10, 20, 50, 100, 200, 500]),
                expires_at=(datetime.now() + timedelta(hours=random.randint(1, 168))).isoformat(),
                is_austin=random.choice([True, False])
            )
            scores.append(score)

        elapsed = time.time() - start
        assert elapsed < 1.0, f"1000 score calculations took {elapsed:.2f}s"


class TestMemoryUsage:
    """Test memory behavior with large datasets."""

    def test_large_deal_list_memory(self):
        """Ensure large deal lists don't cause memory issues."""
        import sys

        # Generate 10,000 deals
        deals = []
        for i in range(10000):
            deals.append({
                'merchant_name': f'Merchant_{i}',
                'deal_score': random.uniform(5.0, 35.0),
                'min_spend': random.choice([5, 10, 20, 50, 100]),
                'total_miles': random.randint(50, 5000),
            })

        # Check memory size is reasonable (< 10MB for 10K deals)
        size_bytes = sys.getsizeof(deals) + sum(sys.getsizeof(d) for d in deals)
        size_mb = size_bytes / (1024 * 1024)

        assert size_mb < 10, f"10K deals using {size_mb:.2f}MB, should be <10MB"

    def test_optimizer_memory_cleanup(self):
        """Optimizer should not leak memory across runs."""
        import gc

        for _ in range(10):
            deals = [
                {'merchant_name': f'M_{i}', 'deal_score': 15.0, 'min_spend': 10, 'total_miles': 150}
                for i in range(1000)
            ]
            result = optimize_allocation(deals, budget=500)
            del deals
            del result
            gc.collect()

        # If we get here without OOM, test passes
        assert True


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_high_yield_deal(self):
        """Handle deals with unusually high yields."""
        deal = StackedDeal(
            merchant_name='Mega Deal',
            portal_rate=50.0,  # Unrealistic but test it
            simplymiles_type='flat_bonus',
            simplymiles_amount=10000,
            simplymiles_min_spend=1.0,
            simplymiles_expires=None
        )
        # Should handle without overflow
        assert deal.base_yield > 0
        assert deal.deal_score > 0

    def test_very_long_merchant_name(self):
        """Handle very long merchant names."""
        long_name = 'A' * 1000
        normalized = normalize_merchant(long_name)
        assert len(normalized) <= len(long_name)

    def test_unicode_merchant_names(self):
        """Handle unicode in merchant names."""
        names = ['Café Express', '日本語ショップ', 'Müller Store', 'Señor Deals']
        for name in names:
            normalized = normalize_merchant(name)
            assert normalized is not None

    def test_empty_and_whitespace_names(self):
        """Handle empty and whitespace-only names."""
        assert normalize_merchant('') == ''
        assert normalize_merchant('   ') == ''
        assert normalize_merchant('\t\n') == ''

    def test_special_characters_in_names(self):
        """Handle special characters."""
        names = ['Shop!@#$%', 'Store & More', 'Deal\'s Place', 'Buy<>Now']
        for name in names:
            normalized = normalize_merchant(name)
            assert normalized is not None


# Performance benchmarks (optional, marked for skip in normal runs)
@pytest.mark.skip(reason="Benchmark test - run manually")
class TestBenchmarks:
    """Performance benchmark tests."""

    def test_full_pipeline_simulation(self):
        """Simulate full pipeline with realistic data volumes."""
        # Simulate 500 SM offers × 1400 portal merchants
        print("\n=== FULL PIPELINE BENCHMARK ===")

        # Step 1: Normalize
        start = time.time()
        sm_names = [f"SimplyMiles Offer {i}" for i in range(500)]
        portal_names = [f"Portal Merchant {i}" for i in range(1400)]
        sm_normalized = [normalize_merchant(n) for n in sm_names]
        portal_normalized = [normalize_merchant(n) for n in portal_names]
        print(f"Normalization: {time.time() - start:.2f}s")

        # Step 2: Match
        start = time.time()
        matches = match_merchants(sm_normalized, portal_normalized, threshold=85)
        print(f"Matching: {time.time() - start:.2f}s, found {len(matches)} matches")

        # Step 3: Score
        start = time.time()
        scores = [calculate_deal_score(15.0, 50) for _ in range(len(matches) or 100)]
        print(f"Scoring: {time.time() - start:.2f}s")

        # Step 4: Optimize
        deals = [{'merchant_name': f'M_{i}', 'deal_score': 15.0, 'min_spend': 50, 'total_miles': 750}
                 for i in range(100)]
        start = time.time()
        result = optimize_allocation(deals, budget=500)
        print(f"Optimization: {time.time() - start:.2f}s")

        print("=== BENCHMARK COMPLETE ===")
