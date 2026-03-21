-- AA Points Monitor - Supabase Schema
-- Run this in Supabase SQL Editor to create all tables

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==================== CORE DATA TABLES ====================

-- SimplyMiles card-linked offers
CREATE TABLE IF NOT EXISTS simplymiles_offers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_name TEXT NOT NULL,
    merchant_name_normalized TEXT NOT NULL,
    offer_type TEXT NOT NULL CHECK (offer_type IN ('flat_bonus', 'per_dollar')),
    miles_amount INTEGER NOT NULL,
    lp_amount INTEGER NOT NULL,
    min_spend DECIMAL(10,2),
    expires_at TIMESTAMPTZ,
    expiring_soon BOOLEAN DEFAULT FALSE,
    scraped_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sm_merchant_norm ON simplymiles_offers(merchant_name_normalized);
CREATE INDEX IF NOT EXISTS idx_sm_scraped ON simplymiles_offers(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_sm_expires ON simplymiles_offers(expires_at);

-- AA Shopping Portal rates
CREATE TABLE IF NOT EXISTS portal_rates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_name TEXT NOT NULL,
    merchant_name_normalized TEXT NOT NULL,
    miles_per_dollar DECIMAL(6,2) NOT NULL,
    is_bonus_rate BOOLEAN DEFAULT FALSE,
    category TEXT,
    url TEXT,
    scraped_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_portal_merchant_norm ON portal_rates(merchant_name_normalized);
CREATE INDEX IF NOT EXISTS idx_portal_scraped ON portal_rates(scraped_at DESC);
CREATE INDEX IF NOT EXISTS idx_portal_rate ON portal_rates(miles_per_dollar DESC);

-- Hotel deals
CREATE TABLE IF NOT EXISTS hotel_deals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hotel_name TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT,
    check_in DATE NOT NULL,
    check_out DATE NOT NULL,
    nightly_rate DECIMAL(10,2) NOT NULL,
    base_miles INTEGER NOT NULL,
    bonus_miles INTEGER DEFAULT 0,
    total_miles INTEGER NOT NULL,
    total_cost DECIMAL(10,2) NOT NULL,
    yield_ratio DECIMAL(6,2) NOT NULL,
    deal_score DECIMAL(6,2) NOT NULL,
    star_rating INTEGER,
    url TEXT,
    scraped_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_hotels_city ON hotel_deals(city);
CREATE INDEX IF NOT EXISTS idx_hotels_checkin ON hotel_deals(check_in);
CREATE INDEX IF NOT EXISTS idx_hotels_score ON hotel_deals(deal_score DESC);

-- Stacked opportunities (Portal + SimplyMiles combined)
CREATE TABLE IF NOT EXISTS stacked_opportunities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_name TEXT NOT NULL,
    portal_rate DECIMAL(6,2) NOT NULL,
    portal_miles INTEGER NOT NULL,
    simplymiles_type TEXT NOT NULL,
    simplymiles_miles INTEGER NOT NULL,
    simplymiles_min_spend DECIMAL(10,2),
    simplymiles_expires TIMESTAMPTZ,
    cc_miles INTEGER NOT NULL,
    min_spend_required DECIMAL(10,2) NOT NULL,
    total_miles INTEGER NOT NULL,
    combined_yield DECIMAL(6,2) NOT NULL,
    deal_score DECIMAL(6,2) NOT NULL,
    computed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stacked_score ON stacked_opportunities(deal_score DESC);
CREATE INDEX IF NOT EXISTS idx_stacked_computed ON stacked_opportunities(computed_at DESC);
CREATE INDEX IF NOT EXISTS idx_stacked_merchant ON stacked_opportunities(merchant_name);

-- Alert history
CREATE TABLE IF NOT EXISTS alert_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_type TEXT NOT NULL CHECK (alert_type IN ('immediate', 'digest')),
    deal_type TEXT NOT NULL CHECK (deal_type IN ('stack', 'hotel', 'portal', 'simplymiles')),
    deal_identifier TEXT NOT NULL,
    deal_score DECIMAL(6,2) NOT NULL,
    sent_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_alert_identifier ON alert_history(deal_identifier, sent_at DESC);
CREATE INDEX IF NOT EXISTS idx_alert_sent ON alert_history(sent_at DESC);

-- Scraper health tracking
CREATE TABLE IF NOT EXISTS scraper_health (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scraper_name TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('success', 'error', 'warning')),
    error_message TEXT,
    items_scraped INTEGER DEFAULT 0,
    run_at TIMESTAMPTZ NOT NULL,
    duration_seconds DECIMAL(8,2),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scraper_health ON scraper_health(scraper_name, run_at DESC);

-- ==================== ANALYTICS TABLES ====================

-- Daily snapshots for trend analysis
CREATE TABLE IF NOT EXISTS daily_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_date DATE NOT NULL UNIQUE,

    -- SimplyMiles metrics
    sm_total_offers INTEGER NOT NULL DEFAULT 0,
    sm_avg_yield DECIMAL(6,2),
    sm_max_yield DECIMAL(6,2),
    sm_expiring_48h INTEGER DEFAULT 0,

    -- Portal metrics
    portal_total_merchants INTEGER NOT NULL DEFAULT 0,
    portal_avg_rate DECIMAL(6,2),
    portal_max_rate DECIMAL(6,2),
    portal_bonus_count INTEGER DEFAULT 0,

    -- Stacked opportunities
    stacked_total INTEGER NOT NULL DEFAULT 0,
    stacked_above_15 INTEGER DEFAULT 0,
    stacked_above_10 INTEGER DEFAULT 0,
    stacked_avg_yield DECIMAL(6,2),
    stacked_max_yield DECIMAL(6,2),

    -- Hotel metrics
    hotel_total_deals INTEGER DEFAULT 0,
    hotel_avg_yield DECIMAL(6,2),
    hotel_max_yield DECIMAL(6,2),

    -- Top deals (JSONB for flexibility)
    top_stacked_deals JSONB,
    top_hotel_deals JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_snapshots_date ON daily_snapshots(snapshot_date DESC);

-- Merchant history for pattern detection
CREATE TABLE IF NOT EXISTS merchant_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    merchant_name_normalized TEXT NOT NULL,
    recorded_date DATE NOT NULL,

    -- Portal data
    portal_rate DECIMAL(6,2),
    portal_is_bonus BOOLEAN,

    -- SimplyMiles data
    sm_offer_type TEXT,
    sm_miles_amount INTEGER,
    sm_lp_amount INTEGER,
    sm_min_spend DECIMAL(10,2),
    sm_expires_at TIMESTAMPTZ,

    -- Computed stacked yield
    stacked_yield DECIMAL(6,2),

    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(merchant_name_normalized, recorded_date)
);

CREATE INDEX IF NOT EXISTS idx_merchant_history_name ON merchant_history(merchant_name_normalized);
CREATE INDEX IF NOT EXISTS idx_merchant_history_date ON merchant_history(recorded_date DESC);
CREATE INDEX IF NOT EXISTS idx_merchant_history_yield ON merchant_history(stacked_yield DESC NULLS LAST);

-- Hotel yield matrix
CREATE TABLE IF NOT EXISTS hotel_yield_matrix (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    city TEXT NOT NULL,
    day_of_week SMALLINT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    duration SMALLINT NOT NULL CHECK (duration BETWEEN 1 AND 7),
    advance_days SMALLINT NOT NULL,

    -- Aggregate stats
    avg_yield DECIMAL(6,2),
    max_yield DECIMAL(6,2),
    min_yield DECIMAL(6,2),
    median_yield DECIMAL(6,2),
    deal_count INTEGER DEFAULT 0,

    -- Top hotels (JSONB)
    top_premium_hotel JSONB,
    top_budget_hotel JSONB,

    -- Metadata
    discovered_at TIMESTAMPTZ,
    last_verified_at TIMESTAMPTZ,
    verification_count INTEGER DEFAULT 1,
    yield_stability DECIMAL(4,3),

    UNIQUE(city, day_of_week, duration, advance_days)
);

CREATE INDEX IF NOT EXISTS idx_yield_matrix_lookup ON hotel_yield_matrix(city, day_of_week, duration, advance_days);
CREATE INDEX IF NOT EXISTS idx_yield_matrix_yield ON hotel_yield_matrix(avg_yield DESC);

-- Status progress tracking
CREATE TABLE IF NOT EXISTS status_progress (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    recorded_date DATE NOT NULL UNIQUE,
    current_lp INTEGER NOT NULL,
    target_lp INTEGER NOT NULL,
    lp_gap INTEGER NOT NULL,

    -- Earnings that day
    lp_earned_today INTEGER DEFAULT 0,
    spend_today DECIMAL(10,2) DEFAULT 0,
    yield_achieved DECIMAL(6,2),

    -- Projections
    projected_lp_eoy INTEGER,
    days_to_target INTEGER,
    avg_daily_lp_needed DECIMAL(6,2),

    -- Deals executed (JSONB array)
    deals_executed JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_status_date ON status_progress(recorded_date DESC);

-- ==================== INTELLIGENCE TABLES ====================

-- Detected patterns for predictions
CREATE TABLE IF NOT EXISTS detected_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_type TEXT NOT NULL CHECK (pattern_type IN (
        'merchant_weekly_cycle',
        'merchant_monthly_cycle',
        'category_trend',
        'hotel_seasonal',
        'expiration_pattern'
    )),
    entity_name TEXT NOT NULL,

    -- Pattern details
    pattern_description TEXT NOT NULL,
    confidence_score DECIMAL(4,3) NOT NULL,

    -- Timing info
    best_day_of_week SMALLINT,
    best_time_of_month TEXT,

    -- Historical evidence
    observations_count INTEGER NOT NULL,
    first_observed TIMESTAMPTZ NOT NULL,
    last_observed TIMESTAMPTZ NOT NULL,

    -- Prediction
    next_predicted_occurrence TIMESTAMPTZ,
    predicted_yield_range JSONB,

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_patterns_type ON detected_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS idx_patterns_entity ON detected_patterns(entity_name);
CREATE INDEX IF NOT EXISTS idx_patterns_next ON detected_patterns(next_predicted_occurrence) WHERE is_active = TRUE;

-- Predictive alerts
CREATE TABLE IF NOT EXISTS predictive_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_type TEXT NOT NULL CHECK (alert_type IN (
        'upcoming_opportunity',
        'pattern_match',
        'rate_increase',
        'expiration_warning'
    )),

    entity_type TEXT NOT NULL,
    entity_name TEXT NOT NULL,

    prediction_text TEXT NOT NULL,
    predicted_for TIMESTAMPTZ NOT NULL,
    confidence_score DECIMAL(4,3) NOT NULL,

    -- Source pattern
    source_pattern_id UUID REFERENCES detected_patterns(id),

    -- Status
    notified BOOLEAN DEFAULT FALSE,
    notified_at TIMESTAMPTZ,
    outcome_verified BOOLEAN DEFAULT FALSE,
    outcome_correct BOOLEAN,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_predictive_upcoming ON predictive_alerts(predicted_for) WHERE notified = FALSE;

-- Credit card comparison rates
CREATE TABLE IF NOT EXISTS cc_comparison_rates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    card_name TEXT NOT NULL,
    category TEXT NOT NULL,
    earning_rate DECIMAL(4,2) NOT NULL,
    point_value DECIMAL(6,4) NOT NULL,
    effective_rate DECIMAL(6,4) NOT NULL,
    notes TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed CC comparison data
INSERT INTO cc_comparison_rates (card_name, category, earning_rate, point_value, effective_rate, notes) VALUES
('Chase Sapphire Reserve', 'Dining', 3.0, 0.015, 0.045, '3x on dining, 1.5cpp via portal'),
('Chase Sapphire Reserve', 'Travel', 3.0, 0.015, 0.045, '3x on travel, 1.5cpp via portal'),
('Amex Gold', 'Dining', 4.0, 0.012, 0.048, '4x on dining, ~1.2cpp'),
('Amex Gold', 'Groceries', 4.0, 0.012, 0.048, '4x on groceries, ~1.2cpp'),
('Citi Double Cash', 'Everything', 2.0, 0.01, 0.02, '2% flat cash back'),
('AA Aviator Red', 'Everything', 1.0, 0.012, 0.012, '1x on everything, ~1.2cpp AA miles'),
('AA Aviator Silver', 'AA Purchases', 2.0, 0.012, 0.024, '2x on AA purchases')
ON CONFLICT DO NOTHING;

-- ==================== ROW LEVEL SECURITY ====================

-- Enable RLS on all tables (optional - for multi-tenant use)
-- ALTER TABLE simplymiles_offers ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE portal_rates ENABLE ROW LEVEL SECURITY;
-- etc.

-- For single-user, just use service role key which bypasses RLS
