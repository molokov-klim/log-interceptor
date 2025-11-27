# LogInterceptor

[![Tests](https://github.com/hash/log-interceptor/workflows/Tests/badge.svg)](https://github.com/hash/log-interceptor/actions)
[![Ruff](https://github.com/hash/log-interceptor/workflows/Ruff/badge.svg)](https://github.com/hash/log-interceptor/actions)
[![Pyright](https://github.com/hash/log-interceptor/workflows/Pyright/badge.svg)](https://github.com/hash/log-interceptor/actions)
[![codecov](https://codecov.io/gh/hash/log-interceptor/branch/main/graph/badge.svg)](https://codecov.io/gh/hash/log-interceptor)
[![Python Version](https://img.shields.io/pypi/pyversions/log-interceptor.svg)](https://pypi.org/project/log-interceptor/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**LogInterceptor** is a Python library for intercepting and monitoring changes in external log files in real-time. Ideal for automated tests and application monitoring.

## ✨ Key Features

- 🚀 **Non-blocking execution** — uses separate threads for monitoring
- 🔍 **Flexible filtering** — support for regex, predicate functions, and composite filters
- 💾 **Memory buffering** — save logs with various overflow strategies
- 🎯 **Callback system** — asynchronous handlers for new entries
- ⏸️ **Pause/Resume** — control log capture without stopping monitoring
- 📊 **Statistics** — track event count, uptime, and metrics
- 🏷️ **Metadata** — timestamp and event_id for each line
- 🛡️ **Reliability** — error handling, file rotation, recovery
- 🌍 **Cross-platform** — works on Linux and Windows
- 🐍 **Python 3.9+** — full type hints support
- 🧪 **Pytest integration** — ready-made fixtures for tests

## 📦 Installation

```bash
pip install log-interceptor
```

For development:

```bash
git clone https://github.com/hash/log-interceptor.git
cd log-interceptor
pip install -e ".[dev]"
```

## 🚀 Quick Start

### Basic Usage

```python
from log_interceptor import LogInterceptor

# Capture new lines written to file
with LogInterceptor(
    source_file="app.log",
    target_file="captured.log"
) as interceptor:
    # Your code that generates logs
    # New entries are automatically copied to captured.log
    pass
```

### Memory Buffering

```python
from log_interceptor import LogInterceptor

interceptor = LogInterceptor(
    source_file="app.log",
    use_buffer=True,
    buffer_size=1000
)

interceptor.start()

# Your code
# ...

# Get captured lines
lines = interceptor.get_buffered_lines()
print(lines)

interceptor.stop()
```

### Log Filtering

```python
from log_interceptor import LogInterceptor
from log_interceptor.filters import RegexFilter

# Capture only ERROR and CRITICAL
error_filter = RegexFilter(r"(ERROR|CRITICAL)", mode="whitelist")

with LogInterceptor(
    source_file="app.log",
    filters=[error_filter],
    use_buffer=True
) as interceptor:
    # Only lines with ERROR or CRITICAL will be captured
    pass
```

### Using Callbacks

```python
from log_interceptor import LogInterceptor

def on_error_logged(line, timestamp, event_id):
    if "ERROR" in line:
        print(f"Error detected: {line}")

interceptor = LogInterceptor(source_file="app.log")
interceptor.add_callback(on_error_logged)
interceptor.start()

# Your code

interceptor.stop()
```

### Pause/Resume for Flow Control

```python
from log_interceptor import LogInterceptor

interceptor = LogInterceptor(source_file="app.log", use_buffer=True)
interceptor.start()

# Capture logs
# ...

# Pause capture for processing
interceptor.pause()
lines = interceptor.get_buffered_lines()
# Process lines...
interceptor.clear_buffer()

# Resume capture
interceptor.resume()

interceptor.stop()
```

### Statistics and Metadata

```python
from log_interceptor import LogInterceptor

with LogInterceptor(source_file="app.log", use_buffer=True) as interceptor:
    # Your code
    # ...
    
    # Get statistics
    stats = interceptor.get_stats()
    print(f"Lines captured: {stats['lines_captured']}")
    print(f"Uptime: {stats['uptime_seconds']:.2f}s")
    
    # Get metadata
    metadata = interceptor.get_lines_with_metadata()
    for entry in metadata:
        print(f"[{entry['event_id']}] {entry['line']}")
```

### Pytest Integration

```python
import pytest
from log_interceptor import LogInterceptor

@pytest.fixture
def log_interceptor(tmp_path):
    """Fixture for log interception in tests"""
    log_file = tmp_path / "app.log"
    log_file.touch()
    
    interceptor = LogInterceptor(
        source_file=log_file,
        use_buffer=True
    )
    interceptor.start()
    
    yield interceptor
    
    interceptor.stop()

def test_application_logs_error(log_interceptor):
    """Verify that application logs errors"""
    # Your code that should generate an ERROR log
    run_application_that_logs_error()
    
    # Check logs
    lines = log_interceptor.get_buffered_lines()
    assert any("ERROR" in line for line in lines)
```

## 🎯 Additional Features

### Context Manager Support

```python
with LogInterceptor(source_file="app.log", target_file="captured.log") as interceptor:
    # Automatic start() on entry
    # Your code
    pass
    # Automatic stop() on exit
```

### Timestamp for Auditing

```python
from log_interceptor import LogInterceptor

with LogInterceptor(
    source_file="app.log",
    target_file="captured.log",
    add_timestamps=True  # ISO 8601 format
) as interceptor:
    # captured.log will contain:
    # [CAPTURED_AT: 2025-11-27T14:30:45.123456+00:00] Log line
    pass
```

### Configuration and Presets

```python
from log_interceptor import LogInterceptor, InterceptorConfig

# Using preset
config = InterceptorConfig.from_preset("aggressive")

# Or custom configuration
config = InterceptorConfig(
    encoding="utf-8",
    buffer_size=5000,
    retry_max_attempts=5
)

interceptor = LogInterceptor(
    source_file="app.log",
    config=config
)
```

## 📚 Documentation

Full documentation is available in the [docs/](docs/) directory:

- [API Reference](docs/API.md) — description of all classes and methods
- [Technical Specifications](Technical%20specifications.md) — detailed technical requirements
- [Development Plan](dev_plan.md) — development plan using TDD methodology

## 🔧 Development

### Environment Setup

```bash
# Clone repository
git clone https://github.com/hash/log-interceptor.git
cd log-interceptor

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=log_interceptor --cov-report=html

# Fast tests only
pytest -m "not slow"
```

### Linting and Type Checking

```bash
# Check code
ruff check .

# Format
ruff format .

# Check types
pyright
```

## 🏗️ Architecture

```
log-interceptor/
├── log_interceptor/          # Main package
│   ├── __init__.py          # Public API
│   ├── interceptor.py       # LogInterceptor class
│   ├── filters.py           # Filter system
│   ├── config.py            # Configuration
│   └── exceptions.py        # Exceptions
├── tests/                    # Tests
│   ├── conftest.py          # Fixtures
│   ├── mock_app.py          # MockLogWriter for tests
│   ├── test_interceptor.py  # LogInterceptor tests
│   └── test_filters.py      # Filter tests
└── docs/                     # Documentation
```

## 🤝 Contributing

We welcome your contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Commit Rules

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — new functionality
- `fix:` — bug fix
- `docs:` — documentation changes
- `test:` — adding or changing tests
- `refactor:` — code refactoring
- `chore:` — configuration changes, CI/CD

## 📋 Requirements

- Python 3.9+
- watchdog >= 3.0.0

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [watchdog](https://github.com/gorakhargosh/watchdog) — for an excellent file system monitoring library
- All project contributors

## 📞 Contact

- GitHub Issues: [https://github.com/hash/log-interceptor/issues](https://github.com/hash/log-interceptor/issues)
- Documentation: [https://github.com/hash/log-interceptor](https://github.com/hash/log-interceptor)

## 🗺️ Roadmap

- [x] Basic file monitoring
- [x] Filter system
- [x] Memory buffering
- [x] Callback system
- [ ] asyncio support
- [ ] Multiple file monitoring
- [ ] Structured logging support (JSON)
- [ ] Web UI for monitoring
