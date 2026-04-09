"""Pytest configuration and common fixtures for tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from log_interceptor.interceptor import LogInterceptor
from tests.mock_app import MockLogWriter

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


@pytest.fixture
def log_interceptor(tmp_path: Path) -> Generator[LogInterceptor, None, None]:
    """Fixture for LogInterceptor with temporary files.

    Args:
        tmp_path: Pytest temporary directory.

    Yields:
        Configured LogInterceptor instance.

    """
    source_file = tmp_path / "app.log"
    source_file.touch()

    interceptor = LogInterceptor(source_file=source_file, use_buffer=True)
    yield interceptor

    if interceptor.is_running():
        interceptor.stop()


@pytest.fixture
def mock_log_writer(tmp_path: Path) -> Generator[MockLogWriter, None, None]:
    """Fixture for MockLogWriter.

    Args:
        tmp_path: Pytest temporary directory.

    Yields:
        Configured MockLogWriter instance.

    """
    log_file = tmp_path / "app.log"
    writer = MockLogWriter(log_file)
    yield writer

    # Cleanup
    if writer.is_running():
        writer.stop()
