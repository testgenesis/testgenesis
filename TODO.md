# TestGenesis TODO

## Code Quality Issues (Non-Critical)

### Linting Issues
- **Line Length Violations (59 remaining)**: Various files exceed 100 character limit
  - Most are in example files (`e2e_amplitude_generator.py`, `generate_*.py`)
  - Some in core amplitude integration files
  - Priority: Low (functionality works, readability impact minimal)

- **Type Annotation Improvements**
  - Use `str | None` instead of `Optional[str]` in some example files
  - Convert remaining `typing.Dict/List` to `dict/list` in older files
  - Priority: Low (modern Python style, no functional impact)

### Architecture & Code Organization

#### Duplicate Code Issues
- **RESOLVED**: ~~`create_test_flow()` function duplicated~~ - CLI now imports from core package
  
- **Medium**: Similar flow extraction logic in both CLI and core packages
  - Consider consolidating into core package with CLI wrapper

#### Error Handling
- **Medium**: Generic exception handling in several flow processing functions
  - Add specific exception types for better debugging
  - Location: `scorer.py` files, flow processing loops

#### Documentation
- **Low**: Missing docstrings in some utility functions
- **Low**: Example files could use more comprehensive documentation

### Testing Gaps

#### Missing Tests
- **Medium**: End-to-end test coverage for full Amplitude → TestGenesis → Generated Test workflow
- **Low**: Edge cases in flow scoring algorithm
- **Low**: Error categorization logic testing

#### Test Organization
- **Low**: Some test files mix unit and integration tests
- **Low**: Test data could be more comprehensive for scoring edge cases

### Security & Configuration

#### Hardcoded Values
- **Medium**: API keys in example files (marked as test keys, but should use env vars)
  - Location: `examples/test-app/.env`, various example scripts
  - **Action**: Ensure all examples use environment variables

#### Configuration Management
- **Low**: Default configuration could be more comprehensive
- **Low**: Configuration validation could be stronger

### Performance

#### Optimization Opportunities
- **Low**: Flow processing could be optimized for large datasets
- **Low**: File I/O operations could be batched in some scenarios

### Developer Experience

#### Tooling
- **Low**: Consider adding pre-commit hooks for linting
- **Low**: Add development setup automation
- **Low**: Improve error messages for common configuration mistakes

#### Documentation
- **Medium**: API documentation could be more comprehensive
- **Low**: Development workflow documentation needs updates

## Feature Enhancements (Future)

### Analytics Platform Support
- **High**: Support for Google Analytics 4
- **Medium**: Support for Mixpanel
- **Medium**: Support for Adobe Analytics
- **Low**: Support for custom analytics platforms

### Test Framework Support
- **Medium**: Support for additional test frameworks beyond Playwright/Cypress
- **Low**: Support for mobile testing frameworks

### Flow Analysis
- **Medium**: Advanced flow similarity detection
- **Medium**: Flow performance metrics integration
- **Low**: Flow business impact auto-detection

### User Experience
- **Medium**: Web UI for flow management and configuration
- **Low**: Visual flow editor
- **Low**: Flow execution monitoring dashboard

## Immediate Next Steps

1. **Fix duplicate `create_test_flow()` function** (CRITICAL)
2. **Commit remaining minor fixes** (missing newlines resolved)
3. **Address hardcoded API keys in examples** (MEDIUM)
4. **Plan architecture consolidation** for CLI/core duplicate logic

---

*Last Updated: 2025-08-17*
*Branch: fix-linting-and-types*