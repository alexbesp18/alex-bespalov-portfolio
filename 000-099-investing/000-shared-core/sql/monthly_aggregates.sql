-- Monthly Aggregates Table for Tier 3 Storage
-- Run this in Supabase SQL Editor

-- Create the monthly_aggregates table
CREATE TABLE IF NOT EXISTS monthly_aggregates (
    id BIGSERIAL PRIMARY KEY,
    month VARCHAR(7) NOT NULL,  -- YYYY-MM format
    symbol VARCHAR(10) NOT NULL,

    -- Price statistics
    open_price DECIMAL(12,4),
    close_price DECIMAL(12,4),
    high_price DECIMAL(12,4),
    low_price DECIMAL(12,4),
    avg_price DECIMAL(12,4),

    -- Indicator averages
    avg_rsi DECIMAL(6,2),
    min_rsi DECIMAL(6,2),
    max_rsi DECIMAL(6,2),
    avg_stoch_k DECIMAL(6,2),
    avg_williams_r DECIMAL(6,2),
    avg_macd DECIMAL(10,4),
    avg_adx DECIMAL(6,2),

    -- Score statistics
    avg_bullish_score DECIMAL(5,2),
    max_bullish_score DECIMAL(5,2),
    avg_reversal_score DECIMAL(5,2),
    max_reversal_score DECIMAL(5,2),
    avg_oversold_score DECIMAL(5,2),
    max_oversold_score DECIMAL(5,2),

    -- Metadata
    trading_days INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique constraint for upsert
    UNIQUE(month, symbol)
);

-- Index for efficient queries
CREATE INDEX IF NOT EXISTS idx_monthly_aggregates_symbol ON monthly_aggregates(symbol);
CREATE INDEX IF NOT EXISTS idx_monthly_aggregates_month ON monthly_aggregates(month);

-- Enable Row Level Security
ALTER TABLE monthly_aggregates ENABLE ROW LEVEL SECURITY;

-- Policy: service role can do everything
CREATE POLICY "Service role full access on monthly_aggregates"
    ON monthly_aggregates
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Optional: anon can read for dashboards
CREATE POLICY "Anon read access on monthly_aggregates"
    ON monthly_aggregates
    FOR SELECT
    TO anon
    USING (true);

-- Optional helper function to find months needing aggregation
CREATE OR REPLACE FUNCTION get_unaggregated_months(cutoff_date DATE)
RETURNS TABLE(month TEXT) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT TO_CHAR(d.date, 'YYYY-MM') as month
    FROM daily_indicators d
    WHERE d.date < cutoff_date
    AND NOT EXISTS (
        SELECT 1 FROM monthly_aggregates m
        WHERE m.month = TO_CHAR(d.date, 'YYYY-MM')
    )
    ORDER BY month;
END;
$$ LANGUAGE plpgsql;
