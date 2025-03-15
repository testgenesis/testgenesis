# TestGenesis

Generate end-to-end tests automatically from user analytics data. TestGenesis analyzes real user behavior patterns and converts them into reliable test suites.

## Features

- 🔄 **Analytics Integration**
  - Extract user flows from Amplitude
  - More platforms coming soon (GA4, Adobe Analytics)
- 🎭 **Test Generation**
  - Generate Playwright tests
  - Generate Cypress tests
  - Configurable assertions and validations
- 🎯 **Smart Flow Detection**
  - Identify common user paths
  - Filter by frequency and importance
  - Handle edge cases and variations

## Project Structure

```
testgenesis/
├── packages/
│   ├── dsl/           # Test flow DSL and code generation
│   └── cli/           # Command-line interface
└── pyproject.toml     # Workspace configuration
```

## Quick Start

```bash
# Install dependencies
uv pip install testgenesis

# Set your Amplitude API key
export AMPLITUDE_API_KEY=your-api-key

# Extract flows from Amplitude
testgenesis amplitude extract-flows \
  --start-date 2024-03-01 \
  --end-date 2024-03-31 \
  --min-frequency 5 \
  --output-dir ./test_flows

# Generate tests
testgenesis generate test_flows/login_flow.json \
  --framework playwright \
  --output tests/e2e/login.spec.ts
```

## Development

### Local Setup

1. Install Python 3.12 or higher
2. Install `uv` for package management
3. Clone and set up the repository:
   ```bash
   # Clone the repository
   git clone https://github.com/testgenesis/testgenesis.git
   cd testgenesis

   # Install in development mode with dev dependencies
   uv pip install -e ".[dev]"

   # If you need to update dependencies later, use:
   uv pip install --upgrade -e ".[dev]"
   ```

### Running the CLI Locally

After installation, you can use the CLI in two ways:

1. Using the installed command:
   ```bash
   # Generate a test from a flow file
   testgenesis path/to/flow.json --framework playwright --output test.spec.ts

   # Extract flows from Amplitude
   testgenesis amplitude extract-flows \
     --api-key your-api-key \
     --start-date 2024-03-01 \
     --end-date 2024-03-31 \
     --output-dir ./test_flows
   ```

2. Using the Python module directly:
   ```bash
   # Generate a test
   python -m testgenesis_cli.commands.generate path/to/flow.json \
     --framework playwright \
     --output test.spec.ts

   # Extract flows
   python -m testgenesis_cli.analytics.amplitude extract-flows \
     --api-key your-api-key \
     --start-date 2024-03-01 \
     --end-date 2024-03-31
   ```

The CLI is installed in development mode (-e), so any changes you make to the code will be immediately reflected without needing to reinstall.

### Running Tests

Use `pytest` to run tests:

```bash
# Run all tests
pytest

# Run specific package tests
pytest packages/cli/tests
pytest packages/dsl/tests

# Run with coverage
pytest --cov=testgenesis_cli --cov=testgenesis_dsl

# Watch mode for CLI tests
pytest-watch packages/cli/tests

# Watch mode for DSL tests
pytest-watch packages/dsl/tests
```

### Code Quality

```bash
# Format code
ruff format .

# Run linter
ruff check .

# Type checking
mypy .
```

## Package Details

### DSL Package (`packages/dsl`)
- Test flow definition language
- Code generation for different test frameworks
- Flow validation and optimization

### CLI Package (`packages/cli`)
- Command-line interface for TestGenesis
- Analytics platform integrations
- Test generation commands

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests to ensure they pass
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

# Coming soon

Integrate with:
1. Google Analytics
2. Adobe Analytics
3. Amplitude
4. Kissmetrics
5. Hotjar
6. UXCam
7. Contentsquare
8. Lookback
9. Mixpanel
10. Mouseflow
11. Crazy Egg
12. FullStory

# Extract flows from Amplitude
testgenesis amplitude extract-flows \
  --api-key your-amplitude-api-key \
  --start-date 2024-03-01 \
  --end-date 2024-03-31

# Generate tests from flows
testgenesis generate test_flows/user_journey_123.json \
  --framework playwright \
  --output tests/e2e/login_flow.spec.ts
```

## Development

### Setup

1. Install Python 3.12 or higher
2. Install `uv` for package management
3. Create and activate a virtual environment
4. Install dependencies: `uv pip install -e ".[dev]"`

### Running Tests

Use `hatch` to run tests:

```bash
# Run tests for CLI package
hatch run test:test packages/cli/tests -v

# Run tests for DSL package
hatch run test:test packages/dsl/tests -v

# Run all tests
hatch run test:test -v

# Watch mode for CLI tests
hatch run test:watch packages/cli/tests -v

# Watch mode for DSL tests
hatch run test:watch packages/dsl/tests -v
```

The test configuration is managed in the root `pyproject.toml` under the `[tool.hatch.envs.test]` section.