# TestGenesis Core

The open-source core of TestGenesis's test generation engine. This package provides fundamental test generation capabilities that can be used standalone or as part of the TestGenesis Cloud platform.

## Features

### Test Generation
- Basic test case generation from UI interactions
- Support for Selenium and Playwright
- Page object model generation
- Test data management

### Test Maintenance
- Simple test healing for minor UI changes
- Test organization and grouping
- Basic reporting

### Integrations
- Selenium WebDriver support
- Playwright support
- pytest integration
- CI/CD examples for popular platforms

## Installation

```bash
pip install testgenesis-core
```

## Quick Start

```python
from testgenesis.core import TestGen

# Initialize test generator
test_gen = TestGen()

# Record a test
with test_gen.record("login_test"):
    driver.get("https://example.com")
    driver.find_element_by_id("username").send_keys("user")
    driver.find_element_by_id("password").send_keys("pass")
    driver.find_element_by_id("submit").click()

# Generate test code
test_gen.generate_test(
    name="test_login",
    framework="pytest",
    driver="selenium"
)
```

## Documentation

For detailed documentation, visit [docs.testgenesis.ai/core](https://docs.testgenesis.ai/core).

### Examples
- [Basic Test Generation](examples/basic_test_generation.py)
- [Page Object Model](examples/page_object_model.py)
- [Custom Test Framework Integration](examples/custom_framework.py)
- [CI/CD Integration](examples/ci_cd_integration.py)

## Contributing

We welcome contributions! Please see our [Contributing Guide](../../CONTRIBUTING.md) for details.

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/testgenesis/testgenesis.git
   cd testgenesis
   ```

2. Install dependencies:
   ```bash
   uv venv
   source .venv/bin/activate
   uv pip install -e "packages/testgen/core[dev]"
   ```

3. Run tests:
   ```bash
   pytest packages/testgen/core/tests
   ```

## Enterprise Features

For advanced features like AI-powered test generation, advanced test healing, and analytics integration, check out [TestGenesis Cloud](https://testgenesis.ai/cloud).

Enterprise features include:
- AI-powered test generation
- Advanced test healing
- Visual testing
- Performance testing
- Cross-browser testing
- Analytics integration
- Team collaboration
- Premium support

## License

This package is licensed under the MIT License. See the [LICENSE](LICENSE) file for details. 