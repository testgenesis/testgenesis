# TestGenesis CLI

Command-line tools for TestGenesis, including analytics integrations and test generation.

## Features

- **Analytics Integration**: Extract user flows from analytics platforms
  - Amplitude integration
  - More platforms coming soon (GA4, Adobe Analytics, etc.)
- **Test Generation**: Generate E2E tests from user flows
  - Playwright support
  - Cypress support
  - Configurable assertions and validations

## Installation

```bash
# Using uv (recommended)
uv pip install testgenesis-cli

# Or using pip
pip install testgenesis-cli
```

## Usage

### Extract Flows from Amplitude

```bash
# Set your Amplitude API key
export AMPLITUDE_API_KEY=your-api-key

# Extract common user flows
testgenesis amplitude extract-flows \
  --start-date 2024-03-01 \
  --end-date 2024-03-31 \
  --min-frequency 5 \
  --output-dir ./test_flows
```

### Generate Tests

```bash
# Generate Playwright test
testgenesis generate test_flows/login_flow.json \
  --framework playwright \
  --output tests/e2e/login.spec.ts

# Generate Cypress test
testgenesis generate test_flows/checkout_flow.json \
  --framework cypress \
  --output cypress/e2e/checkout.cy.ts
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/testgenesis/testgenesis.git
cd testgenesis

# Create virtual environment and install all workspace dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .

# Install dev dependencies
uv pip install pytest>=7.0.0 pytest-cov>=4.1.0 black>=23.0.0 ruff>=0.2.0 mypy>=1.8.0
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_generate.py

# Run with coverage
pytest --cov=testgenesis_cli

# Run with specific markers
pytest -m "not integration"
```

### Code Quality

```bash
# Format code
black .

# Run linter
ruff check .

# Type checking
mypy .
```

### Project Structure

```
testgenesis_cli/
├── analytics/          # Analytics platform integrations
│   └── amplitude.py    # Amplitude API integration
├── commands/          # CLI commands
│   ├── generate.py    # Test generation command
│   └── main.py       # CLI entry point
└── utils/            # Shared utilities
    └── config.py     # Configuration handling

tests/
├── test_amplitude.py  # Amplitude integration tests
└── test_generate.py   # Test generation tests
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests to ensure they pass
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 