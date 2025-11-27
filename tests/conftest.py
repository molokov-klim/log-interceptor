"""Конфигурация pytest и общие фикстуры для тестов."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from log_interceptor.interceptor import LogInterceptor
from mock_app import MockLogWriter

if TYPE_CHECKING:
    from collections.abc import Generator
    from pathlib import Path


@pytest.fixture
def log_interceptor(tmp_path: Path) -> Generator[LogInterceptor, None, None]:
    """Фикстура для LogInterceptor с временными файлами.

    Args:
        tmp_path: Временная директория pytest.

    Yields:
        Настроенный экземпляр LogInterceptor.

    """
    source_file = tmp_path / "app.log"
    source_file.touch()

    interceptor = LogInterceptor(source_file=source_file, use_buffer=True)
    yield interceptor

    if interceptor.is_running():
        interceptor.stop()


@pytest.fixture
def mock_log_writer(tmp_path: Path) -> Generator[MockLogWriter, None, None]:
    """Фикстура для MockLogWriter.

    Args:
        tmp_path: Временная директория pytest.

    Yields:
        Настроенный экземпляр MockLogWriter.

    """
    log_file = tmp_path / "app.log"
    writer = MockLogWriter(log_file)
    yield writer

    # Cleanup
    if writer.is_running():
        writer.stop()
