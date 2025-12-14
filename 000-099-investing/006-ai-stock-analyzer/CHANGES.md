# Changelog

## v1.0.0 - Portfolio Restructure (2025-12-13)

Major restructure for production-ready portfolio presentation.

### 🏗️ Architecture Changes

**Before**: Single 1511-line monolithic file (`technical_analyzer.py`)

**After**: Modular `src/` structure with 10 files:
- `src/main.py` - CLI entry point with argparse
- `src/config.py` - Pydantic-based settings
- `src/analysis/calculator.py` - Technical indicators
- `src/analysis/analyzer.py` - Multi-agent orchestration
- `src/fetcher/twelve_data.py` - Market data fetching
- `src/llm/client.py` - Unified LLM client
- `src/llm/prompts/analysis.txt` - Externalized prompt
- `src/sheets/writer.py` - Google Sheets output

### ✨ New Features

- **CLI Interface** - `python -m src.main AAPL MSFT --verbose`
- **Retry Logic** - Tenacity-based retries with exponential backoff
- **Pydantic Config** - Type-safe configuration with validation
- **Proper Logging** - Replaced 60+ print statements with logging
- **Test Suite** - 24 tests for calculator and config modules

### 📦 New Files

| File | Purpose |
|------|---------|
| `Makefile` | install, run, test, lint commands |
| `pyproject.toml` | Modern Python packaging |
| `tests/` | Pytest test suite |
| `AUDIT_REPORT.md` | Initial audit findings |
| `CHANGES.md` | This file |

### 🔧 Configuration

- Pinned all dependencies in `requirements.txt`
- Added `pydantic-settings` for config management
- Added `tenacity` for retry logic
- Enhanced `.gitignore` for secrets protection

### 📊 Code Quality

| Metric | Before | After |
|--------|--------|-------|
| Files | 1 | 10 |
| Lines/file | 1511 | ~200 avg |
| Type hints | Partial | Complete |
| Docstrings | Partial | Complete |
| Logging | print() | logging |
| Tests | 0 | 24 |
| Retry logic | None | Tenacity |

### 🔒 Security

- No secrets in code (verified)
- `.gitignore` protects all credential files
- `config.json.example` with placeholder values

### 📝 Notes

The legacy `technical_analyzer.py` has been superseded by the modular
`src/` structure but is retained for reference. To use the new version:

```bash
python -m src.main AAPL
```

---

*Restructure performed as part of GitHub portfolio cleanup for AI/ML engineering positions.*
