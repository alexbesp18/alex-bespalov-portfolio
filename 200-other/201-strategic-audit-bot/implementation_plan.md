# Implementation Plan: Strategic Audit Bot

## Phase 1: Infrastructure & Context
- [ ] Create `src/config.py` using `pydantic-settings` for API key management
- [ ] **Test:** Verify environment variables load correctly.

## Phase 2: The Research Service (Incremental)
- [ ] Build `src/services/researcher.py` class:
    - [ ] Method: `get_company_news()`
    - [ ] Method: `get_customer_sentiment()`
    - [ ] Method: `get_competitors()`
- [ ] **Test:** Run `python -m src.services.researcher` to verify JSON output.

## Phase 3: The Strategy Engine (The "Brain")
- [ ] Define Pydantic Models in `src/models/`: `Opportunity`, `StrategyBrief`
- [ ] Build `src/services/strategist.py` with System Prompt (Role: CPO)
- [ ] **Test:** Feed dummy JSON to Engine and check Pydantic validation.

## Phase 4: The Report Generator
- [ ] Create Jinja2 Markdown template (`src/templates/report.md`)
- [ ] Build `src/services/reporter.py` (Fill template -> PDF)
- [ ] **Test:** Generate a PDF from dummy data.

## Phase 5: End-to-End Pipeline
- [ ] Create `main.py` CLI
- [ ] **Final Test:** Run full pipeline on "Stripe".