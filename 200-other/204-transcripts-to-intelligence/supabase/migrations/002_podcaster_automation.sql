-- Migration: Add Podcaster Automation Tables
-- Description: Adds tables for podcaster automation analysis and processing queue
-- Created: 2024-12-22

-- ============================================================================
-- PODCASTER AUTOMATIONS TABLE
-- ============================================================================
-- Stores automation opportunities and their generated solutions for podcasters.

CREATE TABLE IF NOT EXISTS podcaster_automations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Link to the source podcast
    podcast_id UUID REFERENCES podcasts(id) ON DELETE CASCADE,
    
    -- The identified pain point/opportunity
    pain_point TEXT NOT NULL,
    time_spent VARCHAR(50),  -- e.g., "4 hours/week"
    frequency VARCHAR(20),    -- daily/weekly/monthly/occasional
    urgency VARCHAR(10),      -- high/medium/low
    current_solution TEXT,
    automation_potential VARCHAR(10), -- high/medium/low
    supporting_quote TEXT,
    category VARCHAR(50),     -- email/content/scheduling/research/etc.
    
    -- Podcaster context (denormalized for query convenience)
    podcaster_role VARCHAR(100),
    team_size VARCHAR(20),
    tech_savviness VARCHAR(10),
    
    -- Generated solutions (stored as JSONB for flexibility)
    software_spec JSONB,      -- MVP software specification
    workflow JSONB,           -- n8n/Zapier/Make workflow design
    agent_idea JSONB,         -- Custom GPT/Claude/Agent specification
    
    -- Metadata
    llm_cost_usd DECIMAL(10, 6) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for querying by podcast
CREATE INDEX IF NOT EXISTS idx_podcaster_automations_podcast_id 
    ON podcaster_automations(podcast_id);

-- Index for filtering by urgency
CREATE INDEX IF NOT EXISTS idx_podcaster_automations_urgency 
    ON podcaster_automations(urgency);

-- Index for filtering by category
CREATE INDEX IF NOT EXISTS idx_podcaster_automations_category 
    ON podcaster_automations(category);

-- GIN index for JSONB full-text search
CREATE INDEX IF NOT EXISTS idx_podcaster_automations_software_spec 
    ON podcaster_automations USING GIN (software_spec);

-- ============================================================================
-- PROCESSING QUEUE TABLE
-- ============================================================================
-- Stores videos pending processing and their processing history.

CREATE TYPE queue_status AS ENUM (
    'pending',
    'processing',
    'completed',
    'failed',
    'cancelled'
);

CREATE TYPE queue_priority AS ENUM (
    'high',
    'normal',
    'low'
);

CREATE TABLE IF NOT EXISTS processing_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Video identification
    url TEXT NOT NULL,
    video_id VARCHAR(50),     -- Extracted YouTube video ID
    
    -- Processing configuration
    priority queue_priority DEFAULT 'normal',
    options JSONB DEFAULT '{}',  -- Processing options (enrich_ideas, lenses, etc.)
    
    -- Status tracking
    status queue_status DEFAULT 'pending',
    attempts INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 3,
    
    -- Results
    processed_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    output_file TEXT,          -- Path to output JSON
    podcast_id UUID REFERENCES podcasts(id), -- Link to created podcast record
    
    -- Cost tracking
    llm_cost_usd DECIMAL(10, 6) DEFAULT 0,
    
    -- Metadata
    source VARCHAR(50) DEFAULT 'manual',  -- manual/rss/api
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Unique constraint to prevent duplicate URLs in queue
CREATE UNIQUE INDEX IF NOT EXISTS idx_processing_queue_url_pending 
    ON processing_queue(url) 
    WHERE status IN ('pending', 'processing');

-- Index for fetching pending items by priority
CREATE INDEX IF NOT EXISTS idx_processing_queue_pending 
    ON processing_queue(priority, created_at) 
    WHERE status = 'pending';

-- Index for status queries
CREATE INDEX IF NOT EXISTS idx_processing_queue_status 
    ON processing_queue(status);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get next item from queue
CREATE OR REPLACE FUNCTION get_next_queue_item()
RETURNS processing_queue AS $$
DECLARE
    item processing_queue;
BEGIN
    -- Lock and select the next pending item
    SELECT * INTO item
    FROM processing_queue
    WHERE status = 'pending'
      AND attempts < max_attempts
    ORDER BY 
        CASE priority 
            WHEN 'high' THEN 1 
            WHEN 'normal' THEN 2 
            WHEN 'low' THEN 3 
        END,
        created_at
    LIMIT 1
    FOR UPDATE SKIP LOCKED;
    
    -- Mark as processing
    IF item.id IS NOT NULL THEN
        UPDATE processing_queue
        SET status = 'processing',
            attempts = attempts + 1,
            updated_at = NOW()
        WHERE id = item.id;
    END IF;
    
    RETURN item;
END;
$$ LANGUAGE plpgsql;

-- Function to mark item as completed
CREATE OR REPLACE FUNCTION complete_queue_item(
    item_id UUID,
    p_output_file TEXT DEFAULT NULL,
    p_podcast_id UUID DEFAULT NULL,
    p_cost DECIMAL DEFAULT 0
)
RETURNS VOID AS $$
BEGIN
    UPDATE processing_queue
    SET status = 'completed',
        completed_at = NOW(),
        output_file = p_output_file,
        podcast_id = p_podcast_id,
        llm_cost_usd = p_cost,
        updated_at = NOW()
    WHERE id = item_id;
END;
$$ LANGUAGE plpgsql;

-- Function to mark item as failed
CREATE OR REPLACE FUNCTION fail_queue_item(
    item_id UUID,
    p_error TEXT
)
RETURNS VOID AS $$
DECLARE
    item processing_queue;
BEGIN
    SELECT * INTO item FROM processing_queue WHERE id = item_id;
    
    IF item.attempts >= item.max_attempts THEN
        -- Exceeded max attempts, mark as failed
        UPDATE processing_queue
        SET status = 'failed',
            error_message = p_error,
            updated_at = NOW()
        WHERE id = item_id;
    ELSE
        -- Still has retries, mark as pending
        UPDATE processing_queue
        SET status = 'pending',
            error_message = p_error,
            updated_at = NOW()
        WHERE id = item_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER podcaster_automations_updated_at
    BEFORE UPDATE ON podcaster_automations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER processing_queue_updated_at
    BEFORE UPDATE ON processing_queue
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- ROW LEVEL SECURITY (if needed)
-- ============================================================================

-- Enable RLS (uncomment if using authenticated access)
-- ALTER TABLE podcaster_automations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE processing_queue ENABLE ROW LEVEL SECURITY;

-- Example policy (uncomment and modify as needed)
-- CREATE POLICY "Users can view their own automations"
--     ON podcaster_automations
--     FOR SELECT
--     USING (auth.uid() = user_id);

