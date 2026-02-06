# Contributing to lollmsBot

Thank you for your interest in contributing to lollmsBot! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Pull Request Process](#pull-request-process)
- [Areas for Contribution](#areas-for-contribution)

## Code of Conduct

### Our Pledge

We pledge to make participation in lollmsBot a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Positive behaviors include:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Unacceptable behaviors include:**
- Harassment, trolling, or derogatory comments
- Publishing others' private information
- Other conduct which could reasonably be considered inappropriate

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
   ```bash
   git clone https://github.com/YOUR_USERNAME/lollmsBot-GrumpiFied
   cd lollmsBot-GrumpiFied
   ```
3. **Add upstream remote**
   ```bash
   git remote add upstream https://github.com/Grumpified-OGGVCT/lollmsBot-GrumpiFied
   ```

## Development Setup

### Prerequisites
- Python 3.10 or higher
- Git
- Docker (optional, for sandbox features)

### Installation

```bash
# Create virtual environment
python -m venv .venv

# Activate (Linux/macOS)
source .venv/bin/activate

# Activate (Windows)
.venv\Scripts\activate

# Install in development mode with all features
pip install -e ".[all,dev]"

# Run wizard to configure
lollmsbot wizard
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=lollmsbot --cov-report=html

# Run specific test file
pytest tests/test_agent.py

# Run with verbose output
pytest -v
```

### Code Quality Tools

```bash
# Format code
black lollmsbot/

# Sort imports
isort lollmsbot/

# Lint code
flake8 lollmsbot/
pylint lollmsbot/

# Type checking
mypy lollmsbot/
```

## How to Contribute

### Reporting Bugs

Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md) and include:
- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment details
- Error logs (sanitized)
- Screenshots if applicable

### Suggesting Features

Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md) and include:
- Problem statement
- Proposed solution
- Use cases
- Implementation ideas (optional)
- Willingness to contribute

### Security Issues

**DO NOT** open public issues for security vulnerabilities!
- Email maintainers directly
- Use GitHub's private security advisory feature
- See [Security template](.github/ISSUE_TEMPLATE/security_vulnerability.md)

## Coding Standards

### Python Style Guide
- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting (line length: 100)
- Use [isort](https://pycqa.github.io/isort/) for import sorting
- Use type hints for all public APIs

### Documentation Standards
- All public modules, classes, and functions must have docstrings
- Use Google-style docstrings
- Keep docstrings concise but informative
- Include examples for complex functionality

### Example Docstring
```python
def process_message(user_id: str, message: str, context: Optional[Dict] = None) -> Dict[str, Any]:
    """Process a user message through the agent.
    
    Args:
        user_id: Unique identifier for the user
        message: The message text to process
        context: Optional context dictionary with metadata
        
    Returns:
        Dictionary containing:
            - success: bool indicating if processing succeeded
            - response: str with the agent's response
            - metadata: dict with processing information
            
    Raises:
        ValidationError: If user_id or message is invalid
        AgentError: If agent processing fails
        
    Example:
        >>> result = agent.process_message("user123", "Hello!")
        >>> print(result["response"])
        "Hello! How can I help you?"
    """
```

### Code Organization
- Keep modules focused and cohesive
- Limit module size to ~500 lines
- Use clear, descriptive names
- Avoid circular dependencies
- Group related functionality

### Error Handling
- Use specific exception types
- Provide helpful error messages
- Log errors with context
- Don't swallow exceptions silently
- Clean up resources in `finally` blocks

## Testing Guidelines

### Test Structure
- Tests live in `tests/` directory
- Mirror the structure of `lollmsbot/`
- Name test files `test_*.py`
- Name test functions `test_*`

### Test Coverage
- Aim for ≥80% code coverage
- Test happy paths and edge cases
- Test error handling
- Mock external dependencies
- Use fixtures for setup/teardown

### Example Test
```python
import pytest
from lollmsbot.agent import Agent
from lollmsbot.core.exceptions import ValidationError


@pytest.fixture
def agent():
    """Create a test agent instance."""
    return Agent(config=test_config)


def test_valid_message_processing(agent):
    """Test agent processes valid messages correctly."""
    result = agent.process_message("user123", "Hello")
    
    assert result["success"] is True
    assert isinstance(result["response"], str)
    assert len(result["response"]) > 0


def test_invalid_user_id_raises_error(agent):
    """Test agent rejects invalid user IDs."""
    with pytest.raises(ValidationError, match="user_id"):
        agent.process_message("", "Hello")
```

## Pull Request Process

### Before Submitting

1. **Create a branch** from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write clean, documented code
   - Follow coding standards
   - Add/update tests
   - Update documentation

3. **Test your changes**
   ```bash
   pytest
   black --check lollmsbot/
   flake8 lollmsbot/
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add amazing feature"
   ```
   
   **Commit Message Format:**
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation only
   - `style:` Formatting, missing semicolons, etc.
   - `refactor:` Code restructuring
   - `test:` Adding tests
   - `chore:` Maintenance tasks

5. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```

### Submitting the PR

1. **Open a Pull Request** on GitHub
2. **Fill out the PR template** completely
3. **Link related issues** using `Fixes #123`
4. **Request review** from maintainers
5. **Respond to feedback** promptly

### After Submission

- **CI checks must pass** before merging
- **Address review comments** thoroughly
- **Keep PR updated** with main branch
- **Squash commits** if requested

## Areas for Contribution

### High Priority
- **Bug Fixes** - Always welcome!
- **Documentation** - Improve guides, fix typos, add examples
- **Test Coverage** - Increase test coverage in core modules
- **Performance** - Optimize slow operations

### New Features
- **LLM Backends** - Add support for new AI providers
- **Skills** - Create reusable skills for the community
- **Tools** - Integrate new APIs and services
- **Channels** - Add Slack, Matrix, IRC adapters

### Advanced
- **RC2 Capabilities** - Implement remaining sub-agent features
- **Monitoring** - Add Prometheus metrics, Grafana dashboards
- **Caching** - Implement intelligent response caching
- **Multi-language** - Localization support

### Documentation
- **Tutorials** - Step-by-step guides for common tasks
- **Architecture** - Deep dives into system design
- **API Reference** - Complete API documentation
- **Examples** - Real-world usage examples

## Questions?

- **Discord:** Join our community server (link in README)
- **Discussions:** Use GitHub Discussions for questions
- **Issues:** For bug reports and feature requests only

---

**Thank you for contributing to lollmsBot!** 🎉

Every contribution, no matter how small, makes a difference. We appreciate your time and effort in making lollmsBot better for everyone.
