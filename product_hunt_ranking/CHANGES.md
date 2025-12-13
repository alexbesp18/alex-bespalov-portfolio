# Changes Log

## Refactor: Restructure for Production-Ready Portfolio

### Structural Changes
- Reorganized codebase into `src/` directory pattern.
- Separated concerns: `main.py` (orchestration), `config.py` (settings), `utils/parsing.py` (logic).
- Created standard production files: `Makefile`, `.gitignore`, `.env.example`.

### Refinement (High-Bar Engineering)
- **Data Modeling**: Replaced `Dict` with `pydantic.BaseModel` for strict data validation and type safety.
- **CI/CD**: Added GitHub Actions workflow (`.github/workflows/ci.yml`) for automated testing and type checking.
- **Packaging**: Migrated configuration to `pyproject.toml` supporting `ruff`, `mypy`, and `pytest`.
- **Testing**: Enhanced test suite with strict type checks and edge case validation.

### Code Quality
- **Logging**: Replaced all `print()` statements with standard `logging`.
- **Type Hints**: Added comprehensive type annotations to all functions.
- **Configuration**: Migrated hardcoded values to `pydantic-settings` reading from `.env`.
- **Reliability**: Added retry logic to network requests using `tenacity`.
- **Validation**: `mypy` strict mode enabled and passed.

### Documentation
- Completely rewrote `README.md` to professional standards including key features, architecture, and usage.
- Added usage examples and project structure visualizations.

### Testing
- Added `tests/` directory with unit tests for parsing logic and configuration.
- Pinned all dependencies in `requirements.txt`.
