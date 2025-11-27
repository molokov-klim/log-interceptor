"""Тесты для основного класса LogInterceptor."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

from log_interceptor.interceptor import LogInterceptor
from tests.mock_app import MockLogWriter

if TYPE_CHECKING:
    from pathlib import Path


def test_interceptor_initialization(tmp_path: Path) -> None:
    """LogInterceptor должен инициализироваться с путём к файлу."""
    log_file = tmp_path / "app.log"
    log_file.touch()

    interceptor = LogInterceptor(source_file=log_file)

    assert interceptor.source_file == log_file
    assert not interceptor.is_running()


def test_interceptor_requires_existing_file(tmp_path: Path) -> None:
    """LogInterceptor должен требовать существующий файл или allow_missing=True."""
    non_existent = tmp_path / "missing.log"

    # Должно вызвать FileNotFoundError
    error_msg = r"Source file not found"
    with pytest.raises(FileNotFoundError, match=error_msg):
        LogInterceptor(source_file=non_existent)

    # Должно работать с флагом allow_missing=True  # noqa: RUF003
    interceptor = LogInterceptor(source_file=non_existent, allow_missing=True)
    assert interceptor is not None
    assert interceptor.source_file == non_existent


def test_interceptor_start_stop(tmp_path: Path) -> None:
    """LogInterceptor должен корректно запускаться и останавливаться."""
    log_file = tmp_path / "app.log"
    log_file.touch()

    interceptor = LogInterceptor(source_file=log_file)

    interceptor.start()
    assert interceptor.is_running()

    interceptor.stop()
    assert not interceptor.is_running()


def test_interceptor_double_start_raises(tmp_path: Path) -> None:
    """Повторный start() должен вызывать исключение."""
    log_file = tmp_path / "app.log"
    log_file.touch()

    interceptor = LogInterceptor(source_file=log_file)
    interceptor.start()

    error_msg = r"LogInterceptor уже запущен"
    with pytest.raises(RuntimeError, match=error_msg):
        interceptor.start()

    interceptor.stop()


def test_interceptor_captures_new_lines(tmp_path: Path) -> None:
    """LogInterceptor должен захватывать новые строки из файла."""
    source_file = tmp_path / "app.log"
    target_file = tmp_path / "captured.log"

    # Создаём исходный файл с начальным содержимым  # noqa: RUF003
    source_file.write_text("Initial line\n")

    interceptor = LogInterceptor(source_file=source_file, target_file=target_file)
    interceptor.start()

    # MockLogWriter добавляет новые строки
    writer = MockLogWriter(source_file)
    writer.write_line("New line 1")
    writer.write_line("New line 2")

    # Даём время на обработку
    time.sleep(0.5)

    interceptor.stop()

    # Проверяем захваченные строки
    captured = target_file.read_text().splitlines()
    assert "New line 1" in captured
    assert "New line 2" in captured
    assert "Initial line" not in captured  # Не должен захватывать старые  # noqa: RUF003
