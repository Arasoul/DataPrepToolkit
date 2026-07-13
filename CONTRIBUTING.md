# Contributing to DataPrepToolkit

Thank you for your interest in contributing to DataPrepToolkit!

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/DataPrepToolkit.git
   cd DataPrepToolkit
   ```
3. Install in development mode:
   ```bash
   pip install -e ".[dev]"
   ```

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=datapreptoolkit --cov-report=html

# Run specific test file
python -m pytest tests/test_loader.py -v
```

## Code Style

- Python 3.11+ syntax
- Type hints on all public functions
- Google-style docstrings
- PEP 8 compliant
- Use `logging` module instead of `print()`
- Use `pathlib` instead of `os.path`

## Pull Request Process

1. Create a feature branch (`git checkout -b feature/amazing-feature`)
2. Make your changes
3. Add tests for new functionality
4. Ensure all tests pass
5. Update documentation if needed
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Reporting Issues

Please use the GitHub issue tracker to report bugs or request features.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
