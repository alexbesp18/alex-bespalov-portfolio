# PodcastAlpha - YouTube Podcast Intelligence Pipeline

## Project Overview

Transform YouTube podcasts into actionable intelligence: topic summaries, business ideas with full enrichment, multi-lens investment analysis, and podcaster automation opportunities—all with direct quote attribution.

**Key Capabilities:**
- 🎙️ Multi-strategy transcription (YouTube API → yt-dlp → Whisper)
- 💡 Business idea generation with enrichment (niche validation, competitors, lead gen)
- 📈 Multi-lens investment analysis (5 investor perspectives)
- 🤖 Podcaster automation opportunity detection
- 📧 Email notifications via Resend
- 🔄 Automated channel monitoring & queue processing via GitHub Actions

---

## Directory Structure

```
204-transcripts-to-intelligence/
├── .github/
│   └── workflows/
│       └── 204_podcast_intel.yml    # Automated processing workflow
│
├── data/
│   ├── outputs/                     # Generated JSON/Markdown reports
│   └── transcripts/                 # Cached transcripts
│
├── prompts/                         # External prompt files (Markdown + YAML)
│   ├── README.md                    # Prompt authoring guide
│   ├── topics/
│   │   └── extraction.md
│   ├── business/
│   │   ├── idea_generation.md
│   │   ├── lead_gen.md
│   │   ├── niche_validation.md
│   │   └── competitor_check.md
│   ├── investment/
│   │   ├── base_thesis.md
│   │   └── lenses/
│   │       ├── jordi_visser.md
│   │       ├── gavin_baker.md
│   │       ├── leopold_aschenbrenner.md
│   │       ├── karpathy.md
│   │       └── dwarkesh.md
│   └── podcaster_automation/
│       ├── opportunity_detector.md
│       ├── software_specs.md
│       ├── workflow_builder.md
│       └── agent_ideas.md
│
├── scripts/
│   ├── channel_monitor.py           # Detect new videos from channels
│   └── process_queue.py             # Process videos from queue
│
├── src/
│   ├── __init__.py
│   ├── config.py                    # Centralized settings (pydantic-settings)
│   │
│   ├── transcript/                  # MODULE 1: Transcription
│   │   ├── __init__.py
│   │   ├── base.py                  # TranscriptionStrategy ABC
│   │   ├── models.py                # TranscriptionResult, TranscriptSegment
│   │   ├── exceptions.py            # Custom exceptions
│   │   ├── orchestrator.py          # Strategy orchestration
│   │   └── strategies/
│   │       ├── __init__.py
│   │       ├── youtube_api.py       # Level 1: youtube-transcript-api
│   │       ├── ytdlp.py             # Level 2: yt-dlp subtitle extraction
│   │       ├── whisper.py           # Level 3: OpenAI Whisper API
│   │       └── whisper_local.py     # Level 3b: Local faster-whisper
│   │
│   ├── prompts/                     # Prompt Loading System
│   │   ├── __init__.py
│   │   └── loader.py                # PromptLoader with YAML frontmatter
│   │
│   ├── analysis/                    # MODULE 2: LLM Analysis
│   │   ├── __init__.py
│   │   ├── llm_client.py            # OpenAI/Anthropic/OpenRouter clients
│   │   ├── models.py                # TranscriptChunk dataclass
│   │   ├── base.py                  # AnalysisModule ABC, ModuleRegistry
│   │   ├── base_generator.py        # BaseGenerator for DRY LLM calls
│   │   ├── segmenter.py             # TranscriptSegmenter
│   │   ├── topic_extractor.py       # TopicExtractor
│   │   ├── quote_validator.py       # QuoteValidator (fuzzy matching)
│   │   ├── ticker_validator.py      # TickerValidator (yfinance)
│   │   │
│   │   ├── business/                # Business Idea Subpackage
│   │   │   ├── __init__.py
│   │   │   ├── generator.py         # BusinessIdeaGenerator
│   │   │   ├── niche_validator.py   # NicheValidator
│   │   │   ├── competitor_analyzer.py
│   │   │   ├── lead_gen.py          # LeadGenStrategy
│   │   │   └── pipeline.py          # BusinessPipeline orchestrator
│   │   │
│   │   ├── investment/              # Investment Analysis Subpackage
│   │   │   ├── __init__.py
│   │   │   ├── models.py            # InvestorLens, StockPick, etc.
│   │   │   ├── thesis_extractor.py  # InvestmentThesisExtractor
│   │   │   ├── lens_runner.py       # LensRunner (parallel execution)
│   │   │   └── lens_comparator.py   # LensComparator (synthesis)
│   │   │
│   │   └── podcaster_automation/    # Podcaster Automation Subpackage
│   │       ├── __init__.py
│   │       ├── detector.py          # OpportunityDetector
│   │       ├── software_specs.py    # SoftwareSpecsGenerator
│   │       ├── workflow_builder.py  # WorkflowBuilder (n8n/Zapier/Make)
│   │       ├── agent_ideas.py       # AgentIdeaGenerator (GPT/Claude/Agent)
│   │       └── pipeline.py          # PodcasterAutomationPipeline
│   │
│   ├── output/                      # MODULE 3: Output Generation
│   │   ├── __init__.py
│   │   ├── markdown.py              # MarkdownReporter
│   │   └── json_export.py           # JSONExporter
│   │
│   ├── notifications/               # MODULE 4: Notifications
│   │   ├── __init__.py
│   │   ├── base.py                  # BaseNotifier ABC
│   │   ├── manager.py               # NotificationManager
│   │   ├── resend_email.py          # ResendEmailNotifier (primary)
│   │   ├── email.py                 # SendGrid (legacy)
│   │   ├── slack.py                 # SlackNotifier
│   │   └── discord.py               # DiscordNotifier
│   │
│   └── utils/                       # Shared Utilities
│       ├── __init__.py
│       ├── retry.py                 # retry_with_exponential_backoff
│       ├── validation.py            # validate_youtube_url, sanitize_filename
│       ├── logging.py               # Structured logging (structlog)
│       └── cost_tracker.py          # LLMCostTracker
│
├── supabase/
│   └── migrations/
│       └── 002_podcaster_automation.sql
│
├── tests/
│   ├── fixtures/
│   │   └── mock_llm.py              # Mock LLM client for testing
│   ├── test_analysis/
│   │   ├── test_podcaster_automation.py
│   │   ├── test_segmenter.py
│   │   ├── test_topic_extractor.py
│   │   └── test_validators.py
│   ├── test_notifications/
│   │   └── test_notifiers.py
│   └── test_transcript/
│       ├── test_models.py
│       └── test_orchestrator.py
│
├── main.py                          # CLI entry point
├── channels.yaml                    # YouTube channels to monitor
├── queue.yaml                       # Video processing queue
├── requirements.txt
├── pyproject.toml
├── ALL_PROMPTS.md                   # Consolidated prompts for AI brainstorming
└── PROJECT_PLAN.md                  # This file
```

---

## Architecture

### Transcription Strategy Hierarchy

```
┌─────────────────────────────────────────────────────────────────┐
│                   TRANSCRIPTION ORCHESTRATOR                     │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ LEVEL 1: YouTube Transcript API                          │   │
│  │ • Fastest, free, uses youtube-transcript-api             │   │
│  │ • Works for most videos with captions                    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                     │
│                     [If unavailable]                            │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ LEVEL 2: yt-dlp Subtitle Extraction                      │   │
│  │ • More robust, handles edge cases                        │   │
│  │ • Downloads JSON3 subtitle files                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                     │
│                     [If unavailable]                            │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ LEVEL 3a: Local Whisper (faster-whisper)                 │   │
│  │ • Free, runs locally                                     │   │
│  │ • Requires GPU for speed (CPU works but slow)            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                     │
│                     [If unavailable]                            │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ LEVEL 3b: OpenAI Whisper API                             │   │
│  │ • Highest accuracy, costs $0.006/min (~$0.36/hr)         │   │
│  │ • Requires OPENAI_API_KEY                                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Analysis Pipeline Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────────┐
│  Transcript  │────▶│  Segmenter   │────▶│   Topic Extraction   │
│   (full)     │     │ (500 words)  │     │   (per segment)      │
└──────────────┘     └──────────────┘     └──────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────────────┐
│   Business    │   │  Investment   │   │     Podcaster         │
│    Ideas      │   │   Thesis      │   │    Automation         │
└───────────────┘   └───────────────┘   └───────────────────────┘
        │                   │                       │
        ▼                   ▼                       ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────────────┐
│  Enrichment   │   │  Multi-Lens   │   │     Enrichment        │
│  • Niche      │   │  Analysis     │   │  • Software Specs     │
│  • Competitor │   │  (5 lenses)   │   │  • Workflows          │
│  • Lead Gen   │   │               │   │  • Agent Ideas        │
└───────────────┘   └───────────────┘   └───────────────────────┘
        │                   │                       │
        └───────────────────┼───────────────────────┘
                            ▼
                    ┌───────────────┐
                    │    Output     │
                    │  JSON + MD    │
                    └───────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Notification  │
                    │   (Resend)    │
                    └───────────────┘
```

### Investor Lens System

| Lens | Focus | Key Themes |
|------|-------|------------|
| **Jordi Visser** | Macro/Flows | Liquidity, positioning, cross-asset signals |
| **Gavin Baker** | GARP | Unit economics, S-curves, market share |
| **Leopold Aschenbrenner** | AI Compute | AGI timelines, infrastructure, scaling laws |
| **Andrej Karpathy** | Technical AI | Feasibility, data moats, engineering reality |
| **Dwarkesh Patel** | Civilizational | 10+ year trends, historical analogies, tail events |

---

## GitHub Actions Automation

### Workflow: `204_podcast_intel.yml`

```
┌─────────────────────────────────────────────────────────────────┐
│                    DAILY AUTOMATION (6 AM UTC)                  │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ JOB 1: check-channels                                    │   │
│  │ • Read channels.yaml                                     │   │
│  │ • Fetch latest videos via yt-dlp                         │   │
│  │ • Compare against processed list                         │   │
│  │ • Add new videos to queue.yaml                           │   │
│  │ • Commit changes                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            │                                     │
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ JOB 2: process                                           │   │
│  │ • Read queue.yaml                                        │   │
│  │ • Process up to N videos (default: 3)                    │   │
│  │ • Run full analysis pipeline                             │   │
│  │ • Send email notification per video                      │   │
│  │ • Move to processed section                              │   │
│  │ • Commit outputs                                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Manual Triggers:                                               │
│  • skip_channel_check: Process existing queue only              │
│  • video_url: Process single video (bypass queue)               │
│  • enrich_ideas: Enable business enrichment                     │
│  • all_lenses: Run all 5 investor lenses                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Configuration Files

**channels.yaml** - Channels to monitor:
```yaml
channels:
  - name: Peter Diamandis
    url: https://www.youtube.com/@peterdiamandis
    enabled: true
    check_last_n: 5
    options:
      enrich_ideas: true
      all_lenses: true
      podcaster_automation: true
      priority: high
```

**queue.yaml** - Processing queue:
```yaml
videos:
  - url: "https://www.youtube.com/watch?v=..."
    priority: high
    options:
      enrich_ideas: true
      all_lenses: true
    added_at: "2025-12-23T..."
    source_channel: "Peter Diamandis"

processed:
  - url: "https://www.youtube.com/watch?v=..."
    processed_at: "2025-12-23T..."
    status: success
```

---

## External Prompt System

Prompts are stored as Markdown files with YAML frontmatter:

```markdown
---
name: Business Idea Generator
version: 1.0
parameters:
  - transcript
  - num_ideas
temperature: 0.7
max_tokens: 2500
---
# System Prompt

You are a startup strategist...

# User Prompt

Based on this podcast transcript, identify {num_ideas} ideas...
```

**PromptLoader** parses these files and formats prompts with provided parameters.

---

## Cost Estimation

| Component | Cost per 1-hour podcast |
|-----------|------------------------|
| YouTube Captions | Free |
| yt-dlp extraction | Free |
| Local Whisper | Free (slow without GPU) |
| Whisper API (1hr) | ~$0.36 |
| OpenRouter (Claude/GPT) | ~$0.10-0.30 |
| **Total (with captions)** | **$0.10 - $0.30** |
| **Total (with Whisper)** | **$0.46 - $0.66** |

---

## Environment Variables

```bash
# .env (gitignored)

# Required
OPENROUTER_API_KEY=sk-or-v1-...    # Primary LLM provider

# Optional - Fallbacks
OPENAI_API_KEY=sk-proj-...          # For Whisper API
ANTHROPIC_API_KEY=sk-ant-...        # Direct Anthropic access

# Notifications
RESEND_API_KEY=re_...               # Email notifications
EMAIL_FROM=you@domain.com
EMAIL_TO=recipient@domain.com

# Optional
LOG_LEVEL=INFO
```

---

## CLI Usage

```bash
# Process a single video
python main.py "https://youtube.com/watch?v=xxxxx"

# With all enrichment
python main.py "https://youtube.com/watch?v=xxxxx" \
    --enrich-ideas \
    --all-lenses \
    --podcaster-automation

# Specific investor lenses
python main.py "https://youtube.com/watch?v=xxxxx" \
    --lenses jordi_visser gavin_baker

# Process from queue
python scripts/process_queue.py --limit 5

# Check channels for new videos
python scripts/channel_monitor.py --dry-run

# Process single URL via queue script
python scripts/process_queue.py --url "https://youtube.com/watch?v=xxxxx" \
    --enrich-ideas --all-lenses
```

---

## Implementation Status

### ✅ Completed

| Feature | Status |
|---------|--------|
| Multi-strategy transcription | ✅ 4 strategies |
| External prompt system | ✅ PromptLoader + Markdown |
| Topic extraction | ✅ Per-segment analysis |
| Business idea generation | ✅ With enrichment pipeline |
| Investment thesis extraction | ✅ Base + 5 lenses |
| Podcaster automation | ✅ Full pipeline |
| Quote validation | ✅ Fuzzy matching |
| Ticker validation | ✅ yfinance integration |
| JSON/Markdown output | ✅ |
| Email notifications | ✅ Resend |
| GitHub Actions automation | ✅ Daily + manual |
| Channel monitoring | ✅ Auto-detect new videos |
| Queue processing | ✅ Priority-based |
| Retry logic | ✅ Exponential backoff |
| Input validation | ✅ URL + filename sanitization |
| Structured logging | ✅ structlog |
| Cost tracking | ✅ Per-request + daily |

### 🔲 Not Implemented (Future)

| Feature | Priority |
|---------|----------|
| Supabase persistence | Medium |
| Speaker diarization | Low |
| Browser automation (Level 4) | Low |
| Notion integration | Low |
| Web UI | Low |
| Batch file processing | Low |

---

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific module
pytest tests/test_analysis/test_podcaster_automation.py -v
```

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `main.py` | CLI entry point |
| `scripts/process_queue.py` | Queue processor for automation |
| `scripts/channel_monitor.py` | New video detection |
| `src/transcript/orchestrator.py` | Transcription strategy selection |
| `src/analysis/llm_client.py` | LLM provider abstraction |
| `src/prompts/loader.py` | External prompt loading |
| `src/notifications/resend_email.py` | Email notifications |
| `channels.yaml` | Channels to monitor |
| `queue.yaml` | Processing queue state |
| `ALL_PROMPTS.md` | Consolidated prompts for reference |

---

*Last Updated: December 2024*
