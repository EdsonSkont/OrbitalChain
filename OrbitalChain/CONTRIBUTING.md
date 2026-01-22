# Contributing to OrbitalChain

Thank you for your interest in contributing to OrbitalChain! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -e ".[dev]"
   ```

## Development Workflow

### Code Style

- Follow PEP 8 guidelines
- Use type hints for function parameters and return values
- Write docstrings for all public functions and classes
- Maximum line length: 100 characters

### Testing

- Write tests for new functionality
- Ensure all tests pass before submitting:
  ```bash
  pytest tests/ -v
  ```
- Aim for high test coverage:
  ```bash
  pytest tests/ --cov=src --cov-report=html
  ```

### Documentation

- Update documentation for any changed functionality
- Add docstrings following NumPy style
- Update README if adding new features

## Submitting Changes

### Pull Request Process

1. Create a new branch for your feature:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit:
   ```bash
   git add .
   git commit -m "Add: description of your changes"
   ```

3. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

4. Open a Pull Request on GitHub

### Commit Message Format

Use the following prefixes:
- `Add:` for new features
- `Fix:` for bug fixes
- `Update:` for updates to existing features
- `Doc:` for documentation changes
- `Test:` for test additions/changes
- `Refactor:` for code refactoring

### Code Review

- All submissions require review
- Reviewers may request changes
- Be responsive to feedback

## Reporting Issues

### Bug Reports

Include:
- Python version and OS
- Steps to reproduce
- Expected vs actual behavior
- Error messages if any

### Feature Requests

Include:
- Use case description
- Proposed solution
- Alternatives considered

## Areas for Contribution

### High Priority
- Performance optimizations
- Additional test coverage
- Documentation improvements
- Bug fixes

### Features Welcome
- Additional consensus mechanisms
- New channel models
- Visualization tools
- Integration examples

## Questions?

Feel free to open an issue for any questions about contributing.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
