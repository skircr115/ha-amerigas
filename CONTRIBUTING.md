# Contributing to AmeriGas Home Assistant Integration

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Pull Request Process](#pull-request-process)
- [Testing](#testing)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all.

### Our Standards

**Examples of behavior that contributes to creating a positive environment:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Examples of unacceptable behavior:**
- Trolling, insulting/derogatory comments, and personal attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate

---

## How Can I Contribute?

### Reporting Bugs

**Before submitting a bug report:**
- Check existing [Issues](https://github.com/skircr115/ha-amerigas/issues)
- Test with the latest version
- Verify credentials work on MyAmeriGas website

**When submitting, include:**
1. Home Assistant version
2. Integration version
3. Installation method (HACS or manual)
4. Full error message from logs
5. Steps to reproduce
6. Expected vs actual behavior
7. Sensor states (Developer Tools → States)

**Use the bug report template** when creating an issue.

### Suggesting Features

**Before suggesting:**
- Check [Discussions](https://github.com/skircr115/ha-amerigas/discussions)
- Consider if it fits the project scope
- Think about implementation complexity

**When suggesting, include:**
1. Clear description of the feature
2. Use case - why is this needed?
3. Examples - how would it work?
4. Alternatives considered

**Use the feature request template** when creating an issue.

### Contributing Code

**Types of contributions we're looking for:**
- 🐛 Bug fixes
- ✨ New features
- 📝 Documentation improvements
- 🧪 Tests
- 🎨 Dashboard examples
- 🔔 Automation examples

---

## Development Setup

### Prerequisites

- Python 3.11+
- Home Assistant development environment
- Git
- Code editor (VS Code recommended)

### Fork and Clone

```bash
# Fork the repository on GitHub, then:
git clone https://github.com/YOUR_USERNAME/ha-amerigas.git
cd ha-amerigas

# Add upstream remote
git remote add upstream https://github.com/skircr115/ha-amerigas.git

# Create development branch
git checkout -b feature/your-feature-name
```

### Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements_dev.txt

# Install pre-commit hooks
pre-commit install
```

### Testing Your Changes

1. **Copy to HA test instance:**
```bash
cp -r custom_components/amerigas /config/custom_components/
```

2. **Restart Home Assistant**

3. **Configure integration:**
   - Settings → Devices & Services → Add Integration
   - Search "AmeriGas Propane"
   - Enter test credentials

4. **Verify:**
   - All 37 sensors populate
   - No errors in logs
   - Manual update works
   - Automations function

5. **Check logs:**
   - Settings → System → Logs
   - Search for "amerigas"

---

## Coding Standards

### Python

**Follow PEP 8 and Home Assistant conventions:**

```python
# Good
async def async_update_data() -> dict[str, Any]:
    """Fetch data from AmeriGas API."""
    try:
        return await api.async_get_data()
    except AmeriGasAPIError as err:
        raise UpdateFailed(f"Error: {err}") from err

# Bad
async def update():
    data = await api.get()
    return data
```

**Key rules:**
- 4 spaces for indentation (no tabs)
- Max line length: 88 characters (Black formatter)
- Type hints for all function signatures
- Docstrings for all public functions
- Descriptive variable names

**Error Handling:**
```python
# Always use specific exceptions
try:
    response = await session.post(url)
except aiohttp.ClientError as err:
    _LOGGER.error("Network error: %s", err)
    raise CannotConnect from err
except Exception as err:
    _LOGGER.exception("Unexpected error")
    raise
```

**Logging:**
```python
# Use appropriate log levels
_LOGGER.debug("Detailed debug info: %s", data)
_LOGGER.info("Important status: Tank at %s%%", level)
_LOGGER.warning("Warning: %s", issue)
_LOGGER.error("Error occurred: %s", error)
```

### Code Formatting

**Use Black and isort:**
```bash
# Format code
black custom_components/amerigas/
isort custom_components/amerigas/

# Check formatting
black --check custom_components/amerigas/
```

### Type Hints

**Required for all functions:**
```python
from typing import Any

async def async_get_data(self) -> dict[str, Any]:
    """Fetch data."""
    pass

def parse_date(date_str: str) -> datetime | None:
    """Parse date string."""
    pass
```

### Documentation

**Docstrings required:**
```python
def calculate_usage(
    previous: float,
    current: float,
    threshold: float = 0.5
) -> float:
    """
    Calculate propane usage with noise filtering.
    
    Args:
        previous: Previous tank level in gallons
        current: Current tank level in gallons
        threshold: Minimum change to register (default 0.5)
    
    Returns:
        Gallons consumed, or 0 if below threshold
    """
    diff = previous - current
    return diff if diff > threshold else 0.0
```

---

## Pull Request Process

### Before Submitting

**Checklist:**
- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Added tests for new features
- [ ] Updated documentation
- [ ] No breaking changes (or documented)
- [ ] Commit messages follow convention
- [ ] PR description is clear

### Commit Messages

**Use Conventional Commits:**
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code refactoring
- `test`: Tests
- `chore`: Maintenance

**Examples:**
```bash
feat(sensor): add tank monitor battery status sensor

fix(api): handle timeout errors gracefully

docs(readme): update installation instructions

refactor(sensor): improve lifetime tracking logic
```

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tested in development environment
- [ ] All sensors work correctly
- [ ] No errors in logs
- [ ] Automations tested

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)

## Related Issues
Fixes #123
```

### Review Process

1. **Submit PR** to `main` branch
2. **Automated checks** run (linting, tests)
3. **Maintainer review** (within 1 week typically)
4. **Address feedback** if requested
5. **Approval and merge** when ready

---

## Testing

### Manual Testing

**Required tests:**
- [ ] Fresh installation works
- [ ] Configuration via UI successful
- [ ] All 37 sensors populate
- [ ] Values match MyAmeriGas website
- [ ] Manual update works
- [ ] No errors in logs
- [ ] Energy Dashboard integration works
- [ ] Lifetime tracking accurate
- [ ] Restarts preserve state

### Test Environments

**Minimum:**
- Home Assistant Core 2023.1+
- Clean test instance

**Ideal:**
- Multiple HA versions
- Different account types
- With/without tank monitor

### Automated Tests

**Run tests:**
```bash
# Unit tests
pytest tests/

# Type checking
mypy custom_components/amerigas/

# Linting
pylint custom_components/amerigas/
flake8 custom_components/amerigas/
```

---

## Documentation

### Code Comments

```python
# Good: Explain why, not what
# Base64 encode required by AmeriGas API authentication
encoded_email = base64.b64encode(username.encode()).decode()

# Bad: State the obvious
# Encode the email
encoded_email = base64.b64encode(username.encode()).decode()
```

### README Updates

When adding features, update:
- Feature list
- Sensor table
- Configuration examples
- Dashboard examples

---

## Need Help?

### Getting Started

1. Check [README.md](README.md)
2. Read existing code
3. Look at closed PRs
4. Ask in [Discussions](https://github.com/skircr115/ha-amerigas/discussions)

### Questions?

- 💬 [GitHub Discussions](https://github.com/skircr115/ha-amerigas/discussions)
- 🐛 [GitHub Issues](https://github.com/skircr115/ha-amerigas/issues)
- 🏠 [Home Assistant Forum](https://community.home-assistant.io/)

---

## Recognition

All contributors will be:
- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- Appreciated in README

---

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for contributing! 🎉**

**[← Back to README](README.md)**
