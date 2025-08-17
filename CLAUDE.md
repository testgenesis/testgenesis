# CLAUDE.md

⚠️ **MANDATORY WORKFLOW - READ FIRST** ⚠️

## AI Agent Requirements (MUST FOLLOW)

### Before ANY Action:
- [ ] Search YAMS first: `yams search "<query>" --limit 20`
- [ ] Use YAMS for ALL codebase queries (never grep/find/rg)
- [ ] Create 3-7 bullet checklist for multi-step processes

### During Work:
- [ ] Use `yams grep` instead of system grep/find/rg
- [ ] Add ALL discoveries to YAMS with tags
- [ ] Reference by YAMS hash in documentation

### After Changes:
- [ ] Re-index files: `yams add <file> --tags "code,working"`
- [ ] Validate YAMS outcome in 1-2 lines

### FORBIDDEN TOOLS:
- ❌ System grep/find/rg for codebase queries
- ❌ External search before YAMS search
- ❌ File operations without YAMS indexing

---

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TestGenesis is a tool that generates end-to-end tests automatically from user analytics data. It extracts real user behavior patterns from analytics platforms (currently Amplitude, with more coming) and converts them into reliable test suites for Playwright or Cypress.

## Development Commands

### Installation
```bash
# Install with development dependencies using uv
uv pip install -e ".[dev]"

# Update dependencies
uv pip install --upgrade -e ".[dev]"
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific package tests
pytest packages/cli/tests
pytest packages/dsl/tests
pytest packages/core/tests

# Run a single test file
pytest packages/cli/tests/test_generate.py

# Run a single test function
pytest packages/cli/tests/test_generate.py::test_function_name

# Run with coverage
pytest --cov=testgenesis_cli --cov=testgenesis_dsl --cov=testgenesis_core

# Run in verbose mode
pytest -v

# Run without integration tests
pytest -m "not integration"
```

### Code Quality
```bash
# Format code
ruff format .

# Run linter
ruff check .

# Fix linting issues automatically
ruff check . --fix

# Type checking
mypy .
```

### CLI Usage
```bash
# Generate a test from a flow file
testgenesis path/to/flow.json --framework playwright --output test.spec.ts

# Extract flows from Amplitude
testgenesis amplitude extract-flows \
  --api-key your-api-key \
  --start-date 2024-03-01 \
  --end-date 2024-03-31 \
  --output-dir ./test_flows

# Run directly as Python module
python -m testgenesis_cli.cli
```

## Architecture

### Package Structure

The project uses a monorepo structure with three main packages:

1. **`packages/core/`** - Core functionality and shared utilities
   - `testgenesis_core/analytics/` - Analytics platform integrations (Amplitude, scoring)
   - `testgenesis_core/test_utils/` - Test utilities and Hypothesis strategies

2. **`packages/cli/`** - Command-line interface
   - `testgenesis_cli/cli.py` - Main CLI entry point
   - `testgenesis_cli/commands/` - CLI command implementations
   - `testgenesis_cli/analytics/` - Analytics-specific CLI commands (Amplitude flow extraction)

3. **`packages/dsl/`** - Domain-Specific Language for test generation
   - `testgenesis_dsl/models/` - Core data models (TestFlow, Action)
   - `testgenesis_dsl/generators/` - Test code generators for different frameworks (Playwright, Cypress)

### Key Concepts

**TestFlow**: Core abstraction representing a sequence of user actions that form a test case. Flows are extracted from analytics data and converted to test code.

**Action**: Individual user interaction (navigation, form submission, click, etc.) within a TestFlow.

**FlowScorer**: Evaluates and ranks flows based on business impact, frequency, and error patterns to prioritize test generation.

**Generators**: Framework-specific code generators that convert TestFlow objects into executable test code (Playwright or Cypress).

### Data Flow

1. Analytics data is fetched from platforms (e.g., Amplitude)
2. Raw events are processed and grouped into user flows
3. Flows are scored and filtered based on frequency and importance
4. High-value flows are converted to TestFlow objects
5. TestFlow objects are passed to framework-specific generators
6. Generated test code is written to specified output files

### Integration Points

- **Analytics Platforms**: Currently Amplitude via REST API. Future: GA4, Adobe Analytics, Mixpanel, etc.
- **Test Frameworks**: Playwright and Cypress generators in `packages/dsl/testgenesis_dsl/generators/`
- **Configuration**: Flow scoring configuration via YAML files

## Testing Strategy

- Unit tests for each package in their respective `tests/` directories
- Integration tests marked with `@pytest.mark.integration`
- Test utilities and Hypothesis strategies in `testgenesis_core/test_utils/`
- Example app in `examples/test-app/` for end-to-end testing

## Important Files

- `pyproject.toml` - Main project configuration, dependencies, and tool settings
- `pytest.ini` - Test configuration and paths
- `packages/cli/testgenesis_cli/cli.py` - CLI entry point
- `packages/dsl/testgenesis_dsl/generators/` - Test code generation logic
- `packages/core/testgenesis_core/analytics/scorer.py` - Flow scoring and prioritization logic
- Always use uv to manage dependencies and to run python code.
- When adding a package use `uv add` instead of `uv pip install`
- Always make branch names descriptive to changes made

---

## Import YAMS Development Policies

@/Users/ulver/yams/PROMPT-eng.md

*The above import includes the complete YAMS-first development workflow and policies for all Claude Code sessions.*

---

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.