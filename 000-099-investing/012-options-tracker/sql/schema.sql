-- Options Tracker Schema (current as of 2026-03-20)
-- Project: alex_projects (rxsmmrmahnvaarwsngtb)
-- Schema: options_tracker

CREATE SCHEMA IF NOT EXISTS options_tracker;

-- Watchlist: contracts we track
CREATE TABLE IF NOT EXISTS options_tracker.watchlist (
    id BIGSERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    expiration DATE NOT NULL,
    strike NUMERIC(12,4) NOT NULL,
    option_type TEXT NOT NULL DEFAULT 'call',
    label TEXT,
    is_active BOOLEAN DEFAULT true,
    peak_mid NUMERIC(12,4) DEFAULT 0,
    peak_mid_date DATE,
    last_alert_level INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    CONSTRAINT uq_watchlist_contract UNIQUE (ticker, expiration, strike, option_type)
);

-- Daily prices: one row per contract per day
CREATE TABLE IF NOT EXISTS options_tracker.daily_prices (
    id BIGSERIAL PRIMARY KEY,
    watchlist_id BIGINT NOT NULL REFERENCES options_tracker.watchlist(id),
    snapshot_date DATE NOT NULL,
    spot_price NUMERIC(12,4) NOT NULL,
    bid NUMERIC(12,4),
    ask NUMERIC(12,4),
    mid_price NUMERIC(12,4) NOT NULL,
    implied_vol NUMERIC(8,6),
    drawdown_pct NUMERIC(8,4),
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(watchlist_id, snapshot_date)
);

-- Alert history log
CREATE TABLE IF NOT EXISTS options_tracker.alert_log (
    id BIGSERIAL PRIMARY KEY,
    watchlist_id BIGINT NOT NULL REFERENCES options_tracker.watchlist(id),
    alert_date DATE NOT NULL,
    threshold INTEGER NOT NULL,
    drawdown_pct NUMERIC(8,4) NOT NULL,
    mid_price NUMERIC(12,4) NOT NULL,
    peak_ref NUMERIC(12,4) NOT NULL,
    source TEXT NOT NULL DEFAULT 'ATH',
    sent_at TIMESTAMPTZ DEFAULT now()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_prices_date ON options_tracker.daily_prices(snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_alert_log_wl ON options_tracker.alert_log(watchlist_id, alert_date);

-- RLS
ALTER TABLE options_tracker.watchlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE options_tracker.daily_prices ENABLE ROW LEVEL SECURITY;
ALTER TABLE options_tracker.alert_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "read_all_wl" ON options_tracker.watchlist FOR SELECT USING (true);
CREATE POLICY "write_svc_wl" ON options_tracker.watchlist FOR ALL USING (current_setting('role') = 'service_role') WITH CHECK (current_setting('role') = 'service_role');
CREATE POLICY "insert_anon_wl" ON options_tracker.watchlist FOR INSERT WITH CHECK (true);
CREATE POLICY "read_all_dp" ON options_tracker.daily_prices FOR SELECT USING (true);
CREATE POLICY "write_svc_dp" ON options_tracker.daily_prices FOR ALL USING (current_setting('role') = 'service_role') WITH CHECK (current_setting('role') = 'service_role');
CREATE POLICY "read_all_al" ON options_tracker.alert_log FOR SELECT USING (true);
CREATE POLICY "write_svc_al" ON options_tracker.alert_log FOR ALL USING (current_setting('role') = 'service_role') WITH CHECK (current_setting('role') = 'service_role');

-- Grants
GRANT USAGE ON SCHEMA options_tracker TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA options_tracker TO service_role;
GRANT SELECT ON ALL TABLES IN SCHEMA options_tracker TO anon, authenticated;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA options_tracker TO service_role;

-- Batch SQL functions
CREATE OR REPLACE FUNCTION options_tracker.rolling_peaks(p_cutoff DATE, p_ids BIGINT[])
RETURNS TABLE(watchlist_id BIGINT, peak_30d NUMERIC) AS $$
    SELECT watchlist_id, MAX(mid_price) AS peak_30d
    FROM options_tracker.daily_prices
    WHERE watchlist_id = ANY(p_ids) AND snapshot_date >= p_cutoff
    GROUP BY watchlist_id;
$$ LANGUAGE sql STABLE;

CREATE OR REPLACE FUNCTION options_tracker.previous_spots(p_today DATE, p_ids BIGINT[])
RETURNS TABLE(watchlist_id BIGINT, prev_spot NUMERIC, prev_mid NUMERIC) AS $$
    SELECT DISTINCT ON (watchlist_id) watchlist_id, spot_price, mid_price
    FROM options_tracker.daily_prices
    WHERE watchlist_id = ANY(p_ids) AND snapshot_date < p_today
    ORDER BY watchlist_id, snapshot_date DESC;
$$ LANGUAGE sql STABLE;

-- Dashboard view (computes ATH DD, 30d DD, 1d chg from live data)
CREATE OR REPLACE VIEW options_tracker.latest_dashboard AS
WITH ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY watchlist_id ORDER BY snapshot_date DESC) AS rn
    FROM options_tracker.daily_prices
),
latest AS (SELECT * FROM ranked WHERE rn = 1),
prev AS (SELECT * FROM ranked WHERE rn = 2)
SELECT
    w.id AS wl_id, w.label, w.ticker, w.expiration, w.strike,
    w.peak_mid AS ath_peak, w.last_alert_level,
    (w.expiration - CURRENT_DATE) AS dte,
    l.snapshot_date, l.spot_price, l.mid_price, l.bid, l.ask,
    ROUND(((l.mid_price - w.peak_mid) / NULLIF(w.peak_mid, 0) * 100)::numeric, 2) AS dd_ath,
    l.mid_price - p.mid_price AS chg_1d,
    peak30.peak_30d,
    ROUND(((l.mid_price - peak30.peak_30d) / NULLIF(peak30.peak_30d, 0) * 100)::numeric, 2) AS dd_30d
FROM options_tracker.watchlist w
JOIN latest l ON w.id = l.watchlist_id
LEFT JOIN prev p ON w.id = p.watchlist_id
LEFT JOIN LATERAL (
    SELECT MAX(mid_price) AS peak_30d
    FROM options_tracker.daily_prices
    WHERE watchlist_id = w.id AND snapshot_date >= CURRENT_DATE - 30
) peak30 ON true
WHERE w.is_active = true;

GRANT SELECT ON options_tracker.latest_dashboard TO anon, authenticated, service_role;

-- PostgREST schema exposure
ALTER ROLE authenticator SET pgrst.db_schemas = 'public, ai_scanner, options_tracker';
NOTIFY pgrst, 'reload schema';
