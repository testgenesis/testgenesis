# TestGenesis E2E Testing Guide

This guide provides a complete, reusable process for generating Amplitude events and extracting flows using TestGenesis. This workflow can be used for both development and CI/CD pipelines.

## Overview

The E2E testing process consists of:
1. **Event Generation**: Automated browser interactions that generate Amplitude events
2. **Flow Extraction**: Extract user flows from Amplitude analytics data  
3. **Test Generation**: Generate Playwright/Cypress tests from extracted flows
4. **Test Execution**: Run generated tests against your application

## Directory Structure

```
examples/test-app/
├── E2E_TESTING_GUIDE.md           # This guide
├── Makefile                       # Automation commands
├── e2e_amplitude_generator.py     # Full Playwright-based event generator
├── simple_event_generator.py     # Simple page visit generator  
├── generate_mock_flows_fixed.py  # Mock data generator for testing
├── generate_all_tests.py         # Batch test generation
├── app.py                         # Test application
├── test_flows/                    # Generated flow files
│   ├── flow_001_login_success_25freq.json
│   ├── flow_003_shopping_cart_30freq.json
│   └── ...
└── tests/generated/               # Generated test files
    ├── login_success.spec.ts
    └── ...
```

## Quick Start

### 1. Start the Test Application

```bash
cd examples/test-app
make start-app
```

Or manually:
```bash
uv run python app.py
```

### 2. Generate Events (Option A: Real Browser Automation)

```bash
make generate-events
```

Or manually:
```bash
python e2e_amplitude_generator.py --base-url http://localhost:8050 --iterations 3 --headless
```

### 2. Generate Events (Option B: Simple Page Visits)

```bash
python simple_event_generator.py
```

### 3. Generate Mock Flows (For Testing Without Amplitude)

```bash
python generate_mock_flows_fixed.py
```

### 4. Extract Flows from Amplitude

```bash
make extract-flows
```

Or manually:
```bash
testgenesis amplitude extract-flows \\
  --api-key $AMPLITUDE_API_KEY \\
  --secret-key $AMPLITUDE_SECRET_KEY \\
  --start-date $(date -v-1d +%Y-%m-%d) \\
  --end-date $(date +%Y-%m-%d) \\
  --output-dir ./test_flows \\
  --region eu
```

### 5. Generate Tests

```bash
testgenesis generate test_flows/flow_001_login_success_25freq.json \\
  --framework playwright \\
  --output tests/generated/login_success.spec.ts
```

### 6. Complete E2E Flow

```bash
make full-e2e
```

## Automation Options

### Makefile Commands

```bash
# Install dependencies
make install

# Application lifecycle
make start-app
make stop-app

# Event generation
make generate-events

# Flow extraction  
make extract-flows

# Complete pipeline
make full-e2e

# Generate tests from flows
make generate-tests

# Cleanup
make clean
```

### Environment Variables

```bash
export BASE_URL=http://localhost:8050
export AMPLITUDE_API_KEY=your-api-key
export AMPLITUDE_SECRET_KEY=your-secret-key
export OUTPUT_DIR=./test_flows
export ITERATIONS=3
```

## Advanced Usage

### Custom Event Generation

The `e2e_amplitude_generator.py` script provides advanced automation:

```python
from e2e_amplitude_generator import AmplitudeEventGenerator

generator = AmplitudeEventGenerator(base_url="http://localhost:8050")
await generator.setup()

# Execute specific flows
await generator.login_flow(should_fail=False)
await generator.shopping_flow()
await generator.error_flow("checkout")

await generator.teardown()
```

### Custom Flow Types

Create custom flows by extending the mock generator:

```python
def generate_custom_flow():
    return {
        "name": "custom_flow",
        "frequency": 15,
        "actions": [
            {
                "type": "navigation",
                "target": "/custom-page",
                "data": {"timestamp": datetime.now().isoformat()}
            },
            {
                "type": "form", 
                "target": "custom_form",
                "data": {"form_data": "example"}
            }
        ]
    }
```

## CI/CD Integration

### GitHub Actions

The workflow is defined in `.github/workflows/e2e-amplitude.yml`:

```yaml
name: E2E Amplitude Testing
on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  e2e-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup Python & uv
      - name: Install dependencies
      - name: Start test app
      - name: Generate events
      - name: Extract flows
      - name: Generate tests
      - name: Upload artifacts
```

### Environment Setup

Required secrets in GitHub:
- `AMPLITUDE_API_KEY`
- `AMPLITUDE_SECRET_KEY` (if using real Amplitude)

## Generated Test Structure

### Sample Generated Test

```typescript
import { test, expect } from '@playwright/test';

test('login_success_flow_8323', async ({ page }) => {
    await page.goto('/');
    await page.goto('/login');
    await page.fill('login_form [name="timestamp"]', '2025-08-16T23:45:27.355239');
    await page.click('login_form');
    await page.click('login_button');
    await page.goto('/dashboard');
});
```

### Test Flow JSON Structure

```json
{
  "name": "login_success_flow_8323",
  "frequency": 25,
  "actions": [
    {
      "type": "navigation",
      "target": "/",
      "data": {"timestamp": "2025-08-16T23:45:22.355239"}
    },
    {
      "type": "form",
      "target": "login_form", 
      "data": {"timestamp": "2025-08-16T23:45:27.355239"}
    }
  ]
}
```

## Troubleshooting

### Common Issues

1. **Amplitude 403 Error**: Check API key, secret key, and region settings
2. **Test Generation Fails**: Ensure flow JSON has correct format with `type` and `target` fields
3. **App Not Responding**: Check that test app is running on correct port
4. **Network Issues**: Use mock data generator for offline testing

### Debug Mode

Run with verbose output:
```bash
python e2e_amplitude_generator.py --base-url http://localhost:8050 --headless=false
```

View browser interactions by setting `headless=false`.

## Data Flow Verification

### Verify Events Generated
1. Check browser console for Amplitude events
2. View Amplitude dashboard for incoming data
3. Check generated_events.json for event log

### Verify Flows Extracted
1. Check `test_flows/` directory for JSON files
2. Validate flow structure matches expected format
3. Review flow frequency and action sequences

### Verify Tests Generated
1. Check `tests/generated/` for TypeScript files
2. Validate test syntax and structure
3. Run tests against application

## Best Practices

1. **Consistent Naming**: Use descriptive flow names indicating purpose and frequency
2. **Regular Generation**: Run E2E flow generation daily to catch UI changes
3. **Flow Validation**: Review extracted flows before generating tests
4. **Mock Data**: Use mock flows for fast iteration and offline development
5. **Version Control**: Commit generated tests to track changes over time

## Integration Points

### With TestGenesis Core
- Flow scoring based on frequency and errors
- Support for multiple analytics platforms
- Configurable test generation templates

### With CI/CD
- Automated flow extraction on schedule
- Test generation from latest user behavior
- Artifact storage for flow history

### With Development Workflow
- Local testing with mock data
- Hot reload for test app changes
- Integration with existing test suites

## Future Enhancements

1. **Real-time Flow Detection**: Stream analytics for immediate test generation
2. **A/B Test Support**: Generate tests for different user segments  
3. **Error Flow Prioritization**: Automatically prioritize flows with high error rates
4. **Visual Regression**: Integrate screenshot comparison with generated tests
5. **Cross-browser Testing**: Generate tests for multiple browser configurations

This E2E testing framework provides a complete, production-ready solution for analytics-driven test generation that can be adapted to any application and analytics platform.