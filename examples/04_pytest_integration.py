"""Example 4: Pytest integration.

Demonstrates:
- Creating fixtures for tests
- Checking logs in automated tests
- Using temporary paths
- Integration testing
"""

import time
from pathlib import Path

import pytest

from log_interceptor import LogInterceptor
from log_interceptor.filters import RegexFilter


# Example 1: Simple fixture
@pytest.fixture
def log_interceptor(tmp_path: Path):
    """Fixture for capturing logs."""
    log_file = tmp_path / "app.log"
    log_file.touch()

    interceptor = LogInterceptor(
        source_file=log_file,
        use_buffer=True
    )
    interceptor.start()

    yield interceptor

    if interceptor.is_running():
        interceptor.stop()


# Example 2: Fixture with filter
@pytest.fixture
def error_interceptor(tmp_path: Path):
    """Fixture for capturing only errors."""
    log_file = tmp_path / "app.log"
    log_file.touch()

    error_filter = RegexFilter(r"ERROR", mode="whitelist")
    interceptor = LogInterceptor(
        source_file=log_file,
        filters=[error_filter],
        use_buffer=True
    )
    interceptor.start()

    yield interceptor

    interceptor.stop()


# Test example 1: Check logging
def test_application_logs_startup(log_interceptor: LogInterceptor):
    """Check that application logs startup."""
    # Simulate application
    with log_interceptor.source_file.open("a") as f:
        f.write("INFO: Application started\n")
        f.write("INFO: Configuration loaded\n")

    time.sleep(0.3)

    # Check logs
    lines = log_interceptor.get_buffered_lines()
    assert len(lines) >= 2
    assert any("started" in line.lower() for line in lines)


# Test example 2: Check errors
def test_application_handles_errors(error_interceptor: LogInterceptor):
    """Check that application logs errors."""
    # Simulate application with errors
    with error_interceptor.source_file.open("a") as f:
        f.write("INFO: Processing request\n")
        f.write("ERROR: Database connection failed\n")
        f.write("WARNING: Retrying\n")
        f.write("ERROR: Retry failed\n")

    time.sleep(0.3)

    # Check that all errors are captured
    lines = error_interceptor.get_buffered_lines()
    assert len(lines) >= 2
    assert all("ERROR" in line for line in lines)


# Test example 3: Statistics
def test_interceptor_statistics(log_interceptor: LogInterceptor):
    """Check statistics collection."""
    # Generate logs
    with log_interceptor.source_file.open("a") as f:
        for i in range(10):
            f.write(f"INFO: Log entry {i}\n")

    time.sleep(0.3)

    # Check statistics
    stats = log_interceptor.get_stats()
    assert stats["lines_captured"] >= 10
    assert stats["uptime_seconds"] > 0
    assert stats["events_processed"] >= 1


# Test example 4: Pause/Resume
def test_interceptor_pause_resume(log_interceptor: LogInterceptor):
    """Check pause/resume functionality."""
    # Write logs
    with log_interceptor.source_file.open("a") as f:
        f.write("INFO: Before pause\n")

    time.sleep(0.2)

    # Pause
    log_interceptor.pause()
    assert log_interceptor.is_paused()

    # Logs during pause should not be captured
    with log_interceptor.source_file.open("a") as f:
        f.write("INFO: During pause\n")

    time.sleep(0.2)

    # Resume
    log_interceptor.resume()
    assert not log_interceptor.is_paused()

    with log_interceptor.source_file.open("a") as f:
        f.write("INFO: After resume\n")

    time.sleep(0.2)

    # Check
    lines = log_interceptor.get_buffered_lines()
    assert any("Before pause" in line for line in lines)
    assert any("After resume" in line for line in lines)
    assert not any("During pause" in line for line in lines)


# Test example 5: Metadata
def test_interceptor_metadata(log_interceptor: LogInterceptor):
    """Check metadata."""
    # Generate logs
    with log_interceptor.source_file.open("a") as f:
        f.write("INFO: Test log 1\n")
        f.write("INFO: Test log 2\n")
        f.write("INFO: Test log 3\n")

    time.sleep(0.3)

    # Get metadata
    metadata = log_interceptor.get_lines_with_metadata()
    assert len(metadata) >= 3

    # Check structure
    for entry in metadata:
        assert "line" in entry
        assert "timestamp" in entry
        assert "event_id" in entry
        assert isinstance(entry["timestamp"], float)
        assert isinstance(entry["event_id"], int)

    # Check event_id uniqueness
    event_ids = [entry["event_id"] for entry in metadata]
    assert len(event_ids) == len(set(event_ids))


# Run tests
if __name__ == "__main__":
    # For running example directly
    print("To run tests use: pytest examples/04_pytest_integration.py")
    print("\nAvailable tests:")
    print("  - test_application_logs_startup")
    print("  - test_application_handles_errors")
    print("  - test_interceptor_statistics")
    print("  - test_interceptor_pause_resume")
    print("  - test_interceptor_metadata")

