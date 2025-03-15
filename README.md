# TestGenesis

TestGenesis is an AI-powered testing platform that optimizes your test suite by intelligently analyzing, suggesting, and maintaining tests across the entire testing pyramid. It helps teams achieve the perfect balance between coverage, speed, and maintainability through data-driven insights and automated test optimization.

## Features

### Core Test Analysis & Optimization (`packages/core`)
- Comprehensive test suite analysis:
  - Coverage mapping across all test types (unit, integration, E2E, contract)
  - Identification of gaps and overlapping test coverage
  - Performance impact analysis of each test
  - Test flakiness detection and root cause analysis
- Smart test recommendations:
  - Suggests missing tests based on production incidents and user behavior
  - Identifies opportunities to convert slow E2E tests to faster unit/integration tests
  - Recommends contract tests for microservice boundaries
  - Prioritizes test creation based on business impact
- Automated test maintenance:
  - Refactors flaky tests with ML-powered fixes
  - Consolidates overlapping test coverage
  - Optimizes test execution order for faster feedback
  - Maintains optimal pyramid ratios through smart test distribution
- Framework support:
  - Unit: Jest, PyTest, JUnit
  - Integration: REST-assured, SuperTest
  - Contract: Pact, Spring Cloud Contract
  - E2E: Selenium, Playwright
- CI/CD optimization:
  - Intelligent test selection based on code changes
  - Parallel execution planning
  - Test suite runtime optimization
- Test governance and quality metrics

### Common Utilities (`packages/common`)
- Test analytics and metrics collection
- Coverage mapping tools
- Performance profiling
- Configuration management
- Test data management
- API contract validation

### UI Components (`packages/ui`)
- Test pyramid visualization
- Coverage analysis dashboards
- Performance trends and insights
- Test optimization recommendations
- Recording interface

## Installation

```bash
# Install from PyPI
pip install testgenesis

# Or install from source
git clone https://github.com/testgenesis/testgenesis.git
cd testgenesis
uv venv
source .venv/bin/activate
uv pip install -e "packages/core[dev]"
```

## Quick Start

```python
from testgenesis import TestGen, TestAnalyzer

# Initialize TestGenesis
test_gen = TestGen()
analyzer = TestAnalyzer()

# Analyze current test suite
analysis = analyzer.analyze_suite(
    project_root="./",
    frameworks=["jest", "pytest", "playwright"]
)

# Get optimization recommendations
recommendations = analyzer.get_recommendations(
    analysis_id=analysis.id,
    optimization_goals={
        "reduce_runtime": True,
        "improve_coverage": True,
        "reduce_flakiness": True
    }
)

# Apply recommended optimizations
for rec in recommendations:
    if rec.type == "convert_to_unit":
        # Convert E2E test to unit test
        test_gen.convert_test(
            source_test=rec.source_test,
            target_type="unit",
            framework="jest"
        )
    elif rec.type == "add_contract_test":
        # Add missing contract test
        test_gen.generate_contract_test(
            service=rec.service,
            framework="pact"
        )
    elif rec.type == "fix_flaky":
        # Apply ML-powered fix for flaky test
        test_gen.fix_flaky_test(
            test_path=rec.test_path,
            fix_strategy=rec.suggested_fix
        )

# Monitor improvements
metrics = analyzer.get_metrics(analysis.id)
print(f"Runtime reduced by {metrics.runtime_reduction}%")
print(f"Coverage increased by {metrics.coverage_increase}%")
print(f"Flaky tests reduced by {metrics.flakiness_reduction}%")
```

## Documentation

Visit our [documentation](https://docs.testgenesis.com) for:
- Detailed guides and tutorials
- API reference
- Best practices
- Example projects
- Integration guides

## Cloud Features

Need more advanced features? [TestGenesis Cloud](https://testgenesis.com/cloud) offers:
- Advanced test suite analytics:
  - Deep learning-based code analysis
  - Production incident correlation
  - User behavior pattern analysis
  - Microservice dependency mapping
- Intelligent test optimization:
  - Automated test pyramid balancing
  - ML-powered test conversion (E2E → unit/integration)
  - Smart test parallelization
  - Predictive test selection
- Advanced test maintenance:
  - Automated flaky test detection and repair
  - Test impact analysis
  - Duplicate coverage elimination
  - Self-healing test scripts
- Enterprise features:
  - Cross-team test analytics
  - Custom optimization rules
  - Compliance reporting
  - Priority support

## Contributing

We welcome contributions! Before contributing:
1. Read our [Contributing Guide](CONTRIBUTING.md)
2. Check out our [Development Guide](DEVELOPMENT.md)
3. Look at our [Good First Issues](https://github.com/testgenesis/testgenesis/issues?q=is:issue+is:open+label:"good+first+issue")

## Community

- [Discord Community](https://discord.gg/testgenesis)
- [GitHub Discussions](https://github.com/testgenesis/testgenesis/discussions)
- [Twitter](https://twitter.com/testgenesisHQ)
- [Blog](https://testgenesis.com/blog)

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