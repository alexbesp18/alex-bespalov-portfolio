# PodcastAlpha - YouTube Podcast Intelligence Pipeline

## Project Overview

Transform YouTube podcasts into actionable intelligence: topic summaries, business ideas, and investment theses with direct quote attribution.

---

## Directory Structure

```
podcast_alpha/
├── config/
│   ├── __init__.py
│   ├── settings.py              # Environment & API keys
│   └── prompts/                 # LLM prompt templates
│       ├── topic_extraction.txt
│       ├── business_ideas.txt
│       └── investment_thesis.txt
│
├── src/
│   ├── __init__.py
│   │
│   ├── ingestion/               # MODULE 1: Video Ingestion
│   │   ├── __init__.py
│   │   ├── url_parser.py        # Extract video ID, validate URL
│   │   ├── metadata.py          # Title, channel, duration, description
│   │   └── dedup.py             # Check if already processed
│   │
│   ├── transcription/           # MODULE 2: Transcription (Multi-Strategy)
│   │   ├── __init__.py
│   │   ├── strategy_base.py     # Abstract base class
│   │   ├── strategy_captions.py # Level 1: YouTube native captions
│   │   ├── strategy_ytdlp.py    # Level 2: yt-dlp subtitle extraction
│   │   ├── strategy_whisper.py  # Level 3: Download + Whisper
│   │   ├── strategy_browser.py  # Level 4: Browser automation fallback
│   │   ├── orchestrator.py      # Tries strategies in order
│   │   └── diarization.py       # Speaker identification (optional)
│   │
│   ├── analysis/                # MODULE 3: LLM Analysis
│   │   ├── __init__.py
│   │   ├── segmenter.py         # Split transcript into 3-min chunks
│   │   ├── topic_extractor.py   # Key topics + quotes per segment
│   │   ├── business_ideas.py    # 24-hour business ideas + quotes
│   │   ├── investment_thesis.py # Industries, sub-industries, stocks
│   │   ├── quote_validator.py   # Verify quotes exist in transcript
│   │   └── ticker_validator.py  # Validate US stocks (no OTC)
│   │
│   ├── persistence/             # MODULE 4: Storage
│   │   ├── __init__.py
│   │   ├── supabase_client.py   # Supabase connection & queries
│   │   ├── file_storage.py      # Local file backup
│   │   └── models.py            # Data models / schemas
│   │
│   ├── output/                  # MODULE 5: Output Generation
│   │   ├── __init__.py
│   │   ├── markdown.py          # Markdown report
│   │   ├── json_export.py       # Structured JSON
│   │   └── notion.py            # (Future) Notion integration
│   │
│   └── utils/                   # Shared Utilities
│       ├── __init__.py
│       ├── logger.py            # Structured logging
│       ├── cost_tracker.py      # API cost monitoring
│       ├── retry.py             # Retry with exponential backoff
│       └── cache.py             # Caching layer
│
├── data/                        # Local Storage
│   ├── raw/                     # Downloaded audio files (temp)
│   ├── transcripts/             # Cached transcripts
│   ├── outputs/                 # Generated reports
│   └── logs/                    # Application logs
│
├── tests/
│   ├── __init__.py
│   ├── test_ingestion.py
│   ├── test_transcription.py
│   └── test_analysis.py
│
├── main.py                      # CLI entry point
├── requirements.txt
├── .env.example
└── README.md
```

---

## Supabase Schema Design

### Tables

```sql
-- Core podcast tracking
CREATE TABLE podcasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    youtube_id VARCHAR(20) UNIQUE NOT NULL,
    url TEXT NOT NULL,
    title TEXT,
    channel_name TEXT,
    channel_id VARCHAR(30),
    duration_seconds INTEGER,
    publish_date TIMESTAMP,
    description TEXT,
    thumbnail_url TEXT,
    
    -- Processing metadata
    status VARCHAR(20) DEFAULT 'pending', -- pending, processing, completed, failed
    processed_at TIMESTAMP,
    processing_time_seconds FLOAT,
    error_message TEXT,
    
    -- Cost tracking
    transcription_cost DECIMAL(10,4),
    analysis_cost DECIMAL(10,4),
    total_cost DECIMAL(10,4),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Full transcript storage
CREATE TABLE transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    podcast_id UUID REFERENCES podcasts(id) ON DELETE CASCADE,
    
    full_text TEXT NOT NULL,
    word_count INTEGER,
    
    -- Transcription method used
    method VARCHAR(30), -- 'youtube_captions', 'ytdlp', 'whisper', 'browser'
    confidence_score FLOAT, -- 0-1 quality estimate
    
    -- Whisper-specific metadata
    language VARCHAR(10),
    whisper_model VARCHAR(20), -- 'base', 'small', 'medium', 'large'
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3-minute segment analysis
CREATE TABLE segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    podcast_id UUID REFERENCES podcasts(id) ON DELETE CASCADE,
    
    segment_index INTEGER NOT NULL, -- 0, 1, 2, ...
    start_time_seconds INTEGER NOT NULL,
    end_time_seconds INTEGER NOT NULL,
    
    -- Segment content
    transcript_chunk TEXT NOT NULL,
    
    -- Analysis results
    key_topics JSONB, -- Array of topics
    summary TEXT,
    direct_quote TEXT NOT NULL, -- Required quote
    quote_speaker TEXT, -- If diarization available
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Business ideas output
CREATE TABLE business_ideas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    podcast_id UUID REFERENCES podcasts(id) ON DELETE CASCADE,
    
    idea_index INTEGER NOT NULL, -- 1, 2, 3
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    
    -- 24-hour execution plan
    hour_1_4 TEXT,
    hour_5_12 TEXT,
    hour_13_24 TEXT,
    
    -- Required attribution
    supporting_quote TEXT NOT NULL,
    quote_timestamp_seconds INTEGER,
    
    -- Enrichment
    estimated_startup_cost TEXT,
    target_market TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Investment thesis output
CREATE TABLE investment_theses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    podcast_id UUID REFERENCES podcasts(id) ON DELETE CASCADE,
    
    industry TEXT NOT NULL,
    sub_industry TEXT NOT NULL,
    thesis_summary TEXT NOT NULL,
    time_horizon TEXT DEFAULT '6-18 months',
    
    -- Supporting evidence from podcast
    supporting_quote TEXT NOT NULL,
    catalyst_events TEXT, -- What drives the thesis
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Stock recommendations (linked to thesis)
CREATE TABLE stock_picks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thesis_id UUID REFERENCES investment_theses(id) ON DELETE CASCADE,
    podcast_id UUID REFERENCES podcasts(id) ON DELETE CASCADE,
    
    ticker VARCHAR(10) NOT NULL,
    company_name TEXT NOT NULL,
    exchange VARCHAR(10) NOT NULL, -- NYSE, NASDAQ only
    
    -- Validation
    is_validated BOOLEAN DEFAULT FALSE, -- Confirmed real, not OTC
    market_cap_billions DECIMAL(10,2),
    
    -- Why this stock
    rationale TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Ensure no OTC
    CONSTRAINT valid_exchange CHECK (exchange IN ('NYSE', 'NASDAQ', 'AMEX'))
);

-- Processing audit log
CREATE TABLE processing_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    podcast_id UUID REFERENCES podcasts(id) ON DELETE CASCADE,
    
    step VARCHAR(50), -- 'ingestion', 'transcription', 'analysis', etc.
    status VARCHAR(20), -- 'started', 'completed', 'failed'
    message TEXT,
    duration_ms INTEGER,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX idx_podcasts_youtube_id ON podcasts(youtube_id);
CREATE INDEX idx_podcasts_status ON podcasts(status);
CREATE INDEX idx_podcasts_channel ON podcasts(channel_name);
CREATE INDEX idx_segments_podcast ON segments(podcast_id);
CREATE INDEX idx_stock_picks_ticker ON stock_picks(ticker);
```

---

## Transcription Strategy Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                   TRANSCRIPTION ORCHESTRATOR                     │
│                                                                  │
│  For each strategy, check availability and quality:             │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ LEVEL 1: YouTube Native Captions (youtube-transcript-api) │   │
│  │ • Fastest, free                                          │   │
│  │ • Only works if video has captions enabled               │   │
│  │ • Quality varies (auto-generated vs manual)              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                     │
│                     [If unavailable]                            │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ LEVEL 2: yt-dlp Subtitle Extraction                      │   │
│  │ • More robust subtitle fetching                          │   │
│  │ • Can get auto-generated captions yt-transcript misses   │   │
│  │ • Handles more edge cases                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                     │
│                     [If unavailable]                            │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ LEVEL 3: Audio Download + Whisper                        │   │
│  │ • Download audio via yt-dlp                              │   │
│  │ • Transcribe with OpenAI Whisper API or local model      │   │
│  │ • Most accurate, but costs money / takes time            │   │
│  │ • Options: whisper-1 API, whisper.cpp local              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                     │
│                     [If all else fails]                         │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ LEVEL 4: Browser Automation (Playwright)                 │   │
│  │ • Last resort for DRM-protected or unusual videos        │   │
│  │ • Play video, capture audio, run through Whisper         │   │
│  │ • Slowest, most resource-intensive                       │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## LLM Prompt Strategy

### Topic Extraction (per 3-min segment)

```
You are analyzing a podcast transcript segment. Extract:

1. KEY TOPICS: List 2-4 main topics discussed in this segment
2. SUMMARY: 2-3 sentence summary of the discussion
3. DIRECT QUOTE: Select the single most insightful or actionable quote
   - Must be VERBATIM from the transcript
   - Include speaker if identifiable
   - Aim for 1-3 sentences

Segment [{segment_index}]: {start_time} - {end_time}
---
{transcript_chunk}
---

Respond in JSON format:
{
  "topics": ["topic1", "topic2"],
  "summary": "...",
  "quote": {
    "text": "exact verbatim quote",
    "speaker": "speaker name or 'Unknown'"
  }
}
```

### Business Ideas Prompt

```
You are a startup strategist. Based on this podcast transcript, identify 
3 business ideas that could be started within 24 hours with minimal capital.

Requirements:
1. Each idea must be DIRECTLY inspired by content in the podcast
2. Each idea must include a VERBATIM supporting quote from the transcript
3. Ideas should be actionable within 24 hours
4. Focus on: services, digital products, arbitrage, or consulting

Transcript:
---
{full_transcript}
---

For each idea, provide:
{
  "ideas": [
    {
      "title": "Business name/concept",
      "description": "What it is and why it works",
      "supporting_quote": "EXACT quote from transcript",
      "24_hour_plan": {
        "hours_1_4": "Immediate actions",
        "hours_5_12": "Build/setup phase", 
        "hours_13_24": "Launch/test phase"
      },
      "estimated_cost": "$X-$Y",
      "target_market": "Who you're selling to"
    }
  ]
}
```

### Investment Thesis Prompt

```
You are a senior equity research analyst. Based on this podcast transcript,
identify 5 investment themes for US public markets over the next 6-18 months.

Requirements:
1. Each theme must be supported by content discussed in the podcast
2. Each theme needs a VERBATIM supporting quote
3. Only recommend stocks traded on NYSE, NASDAQ, or AMEX (NO OTC/Pink Sheets)
4. For each theme, recommend 3 specific stocks with rationale

Transcript:
---
{full_transcript}
---

Output format:
{
  "themes": [
    {
      "industry": "Broad industry (e.g., 'Technology')",
      "sub_industry": "Specific sub-sector (e.g., 'AI Infrastructure')",
      "thesis": "Why this sector will outperform",
      "supporting_quote": "EXACT quote from transcript",
      "catalysts": ["catalyst1", "catalyst2"],
      "stocks": [
        {
          "ticker": "NVDA",
          "company": "NVIDIA Corporation",
          "exchange": "NASDAQ",
          "rationale": "Why this specific stock"
        }
      ]
    }
  ]
}
```

---

## Quote Validation Strategy

**Critical**: LLMs hallucinate quotes. Every quote must be validated.

```python
def validate_quote(quote: str, transcript: str, threshold: float = 0.85) -> bool:
    """
    Validate that a quote actually exists in the transcript.
    
    Strategy:
    1. Exact match (ideal)
    2. Fuzzy match with high threshold (handles minor transcription errors)
    3. Semantic similarity as last resort
    """
    # 1. Exact match
    if quote.lower() in transcript.lower():
        return True
    
    # 2. Fuzzy match (handle punctuation, minor word differences)
    from rapidfuzz import fuzz
    
    # Sliding window search
    quote_words = len(quote.split())
    transcript_words = transcript.split()
    
    for i in range(len(transcript_words) - quote_words + 1):
        window = ' '.join(transcript_words[i:i + quote_words])
        similarity = fuzz.ratio(quote.lower(), window.lower()) / 100
        if similarity >= threshold:
            return True
    
    return False
```

---

## Ticker Validation Strategy

```python
import yfinance as yf

VALID_EXCHANGES = {'NYQ', 'NMS', 'NGM', 'ASE'}  # NYSE, NASDAQ, AMEX

def validate_ticker(ticker: str) -> dict:
    """
    Validate a stock ticker is:
    1. Real
    2. Traded on major US exchange (not OTC)
    3. Currently active
    """
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        exchange = info.get('exchange', '')
        
        return {
            'valid': exchange in VALID_EXCHANGES,
            'ticker': ticker,
            'company': info.get('shortName', ''),
            'exchange': exchange,
            'market_cap': info.get('marketCap', 0),
            'is_otc': exchange in {'PNK', 'OTC'},
            'error': None
        }
    except Exception as e:
        return {
            'valid': False,
            'ticker': ticker,
            'error': str(e)
        }
```

---

## Cost Estimation

| Component | Cost per 1-hour podcast |
|-----------|------------------------|
| YouTube Captions | Free |
| yt-dlp extraction | Free |
| Whisper API (1hr audio) | ~$0.36 |
| Whisper local (large) | Free (but slow) |
| Claude Sonnet analysis | ~$0.15-0.30 |
| Supabase | Free tier sufficient |
| **Total** | **$0.15 - $0.66** |

---

## Implementation Phases

### Phase 1: Core Pipeline (Week 1)
- [ ] Project structure setup
- [ ] Config management (.env, settings)
- [ ] Ingestion module (URL parsing, metadata)
- [ ] Transcription Level 1 & 2 (captions, yt-dlp)
- [ ] Basic Supabase schema
- [ ] File storage backup

### Phase 2: Whisper Integration (Week 2)
- [ ] Transcription Level 3 (Whisper API)
- [ ] Local Whisper option (whisper.cpp)
- [ ] Transcription orchestrator
- [ ] Caching layer

### Phase 3: Analysis Engine (Week 2-3)
- [ ] Segmenter (3-min chunks)
- [ ] Topic extraction LLM
- [ ] Business ideas LLM
- [ ] Investment thesis LLM
- [ ] Quote validation
- [ ] Ticker validation

### Phase 4: Output & Polish (Week 3)
- [ ] Markdown report generation
- [ ] JSON export
- [ ] CLI improvements
- [ ] Error handling & retry logic
- [ ] Cost tracking
- [ ] Logging infrastructure

### Phase 5: Advanced Features (Week 4+)
- [ ] Speaker diarization
- [ ] Browser automation fallback
- [ ] Batch processing
- [ ] Notion integration
- [ ] Web UI (optional)

---

## Usage Example

```bash
# Process a single podcast
python main.py process "https://youtube.com/watch?v=xxxxx"

# Process with specific options
python main.py process "https://youtube.com/watch?v=xxxxx" \
    --transcription-method whisper \
    --whisper-model large \
    --output-format markdown

# Batch process from file
python main.py batch podcasts.txt

# Check status of processing
python main.py status --video-id xxxxx

# Re-run analysis only (skip transcription)
python main.py analyze --video-id xxxxx
```

---

## Environment Variables

```bash
# .env
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_KEY=xxxxx

OPENAI_API_KEY=xxxxx          # For Whisper API
ANTHROPIC_API_KEY=xxxxx       # For Claude analysis

# Optional
WHISPER_LOCAL=true            # Use local whisper instead of API
WHISPER_MODEL=large           # base, small, medium, large
LOG_LEVEL=INFO
```
