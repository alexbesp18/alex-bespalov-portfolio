-- AI Model Scanner schema
-- Supabase project: alex_projects
-- Schema: ai_scanner

CREATE SCHEMA IF NOT EXISTS ai_scanner;

-- ======================
-- MODELS (daily snapshot)
-- ======================
CREATE TABLE IF NOT EXISTS ai_scanner.models (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_date           DATE NOT NULL,
    provider            TEXT NOT NULL,
    model_name          TEXT NOT NULL,
    model_id            TEXT NOT NULL,
    tier                TEXT NOT NULL CHECK (tier IN ('fast', 'flagship', 'deep')),

    -- Pricing (USD per 1M tokens)
    input_price         NUMERIC(12,4),
    output_price        NUMERIC(12,4),

    -- Specs
    context_window      INTEGER,

    -- Capabilities (from OpenRouter supported_parameters + modality)
    has_tools           BOOLEAN DEFAULT false,
    has_vision          BOOLEAN DEFAULT false,
    has_reasoning       BOOLEAN DEFAULT false,
    has_web_search      BOOLEAN DEFAULT false,
    has_json_output     BOOLEAN DEFAULT false,
    is_open_weight      BOOLEAN DEFAULT false,
    is_openai_compat    BOOLEAN DEFAULT true,

    -- Meta
    source              TEXT DEFAULT 'openrouter',
    is_new              BOOLEAN DEFAULT false,

    created_at          TIMESTAMPTZ DEFAULT now(),
    UNIQUE(scan_date, provider, model_id)
);

-- RLS enabled for convention compliance (service-role-only access, no policies needed)
ALTER TABLE ai_scanner.models ENABLE ROW LEVEL SECURITY;

-- ======================
-- PICKS (20 recommendations, recomputed daily)
-- ======================
CREATE TABLE IF NOT EXISTS ai_scanner.picks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_date       DATE NOT NULL,
    use_case        TEXT NOT NULL,
    model_id        TEXT NOT NULL,
    model_name      TEXT NOT NULL,
    provider        TEXT NOT NULL,
    input_price     NUMERIC(12,4),
    output_price    NUMERIC(12,4),
    context_window  INTEGER,
    why             TEXT,

    created_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(scan_date, use_case)
);

ALTER TABLE ai_scanner.picks ENABLE ROW LEVEL SECURITY;

-- ======================
-- PROJECTS (what each project currently uses)
-- ======================
CREATE TABLE IF NOT EXISTS ai_scanner.projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_name    TEXT NOT NULL,
    task            TEXT NOT NULL,
    current_model   TEXT NOT NULL,
    current_provider TEXT NOT NULL,
    monthly_est_cost NUMERIC(10,2),
    needs_tools     BOOLEAN DEFAULT false,
    needs_search    BOOLEAN DEFAULT false,
    needs_vision    BOOLEAN DEFAULT false,
    needs_reasoning BOOLEAN DEFAULT false,
    min_context     INTEGER DEFAULT 0,
    updated_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE(project_name, task)
);

ALTER TABLE ai_scanner.projects ENABLE ROW LEVEL SECURITY;

-- ======================
-- VIEWS
-- ======================
CREATE OR REPLACE VIEW ai_scanner.latest AS
SELECT * FROM ai_scanner.models
WHERE scan_date = (SELECT MAX(scan_date) FROM ai_scanner.models);

CREATE OR REPLACE VIEW ai_scanner.latest_picks AS
SELECT * FROM ai_scanner.picks
WHERE scan_date = (SELECT MAX(scan_date) FROM ai_scanner.picks);

-- The money query: for each project, find cheaper alternatives
CREATE OR REPLACE VIEW ai_scanner.upgrade_suggestions AS
SELECT
    p.project_name,
    p.task,
    p.current_model,
    p.current_provider,
    cur.input_price AS current_input_price,
    cur.output_price AS current_output_price,
    alt.model_id AS suggested_model,
    alt.provider AS suggested_provider,
    alt.input_price AS suggested_input_price,
    alt.output_price AS suggested_output_price,
    ROUND(((cur.input_price - alt.input_price) / NULLIF(cur.input_price, 0) * 100)::numeric, 1) AS savings_pct,
    alt.context_window AS suggested_context
FROM ai_scanner.projects p
LEFT JOIN ai_scanner.latest cur
    ON cur.model_id = p.current_model
LEFT JOIN LATERAL (
    SELECT m.* FROM ai_scanner.latest m
    WHERE m.input_price < COALESCE(cur.input_price, 999)
      AND (NOT p.needs_tools OR m.has_tools)
      AND (NOT p.needs_search OR m.has_web_search)
      AND (NOT p.needs_vision OR m.has_vision)
      AND (NOT p.needs_reasoning OR m.has_reasoning)
      AND (m.context_window IS NULL OR m.context_window >= p.min_context)
    ORDER BY (m.input_price + m.output_price) ASC
    LIMIT 1
) alt ON TRUE
WHERE alt.input_price IS NOT NULL
  AND alt.input_price < COALESCE(cur.input_price, 999);

-- Quick lookup function with optional historical date
CREATE OR REPLACE FUNCTION ai_scanner.pick(p_use_case TEXT, p_date DATE DEFAULT NULL)
RETURNS TABLE(
    model_name TEXT,
    model_id TEXT,
    provider TEXT,
    input_price NUMERIC,
    output_price NUMERIC,
    context_window INTEGER,
    why TEXT
)
AS $$
    SELECT r.model_name, r.model_id, r.provider, r.input_price, r.output_price, r.context_window, r.why
    FROM ai_scanner.picks r
    WHERE r.use_case = p_use_case
      AND r.scan_date = COALESCE(p_date, (SELECT MAX(scan_date) FROM ai_scanner.picks))
$$ LANGUAGE sql STABLE;

-- ======================
-- INDEXES
-- ======================
CREATE INDEX IF NOT EXISTS idx_models_scan_date ON ai_scanner.models(scan_date);
CREATE INDEX IF NOT EXISTS idx_picks_scan_date ON ai_scanner.picks(scan_date);
CREATE INDEX IF NOT EXISTS idx_projects_name ON ai_scanner.projects(project_name);
