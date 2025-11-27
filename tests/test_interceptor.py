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


def test_interceptor_memory_buffer(tmp_path: Path) -> None:
    """LogInterceptor должен хранить строки в памяти."""
    source_file = tmp_path / "app.log"
    source_file.write_text("Old line\n")

    interceptor = LogInterceptor(source_file=source_file, use_buffer=True, buffer_size=100)
    interceptor.start()

    writer = MockLogWriter(source_file)
    writer.write_line("Line 1")
    writer.write_line("Line 2")

    time.sleep(0.3)

    lines = interceptor.get_buffered_lines()
    assert len(lines) >= 2
    assert "Line 1\n" in lines
    assert "Line 2\n" in lines

    interceptor.stop()


def test_interceptor_buffer_overflow_fifo(tmp_path: Path) -> None:
    """Буфер должен удалять старые строки при переполнении (FIFO)."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    interceptor = LogInterceptor(
        source_file=source_file,
        use_buffer=True,
        buffer_size=3,
        overflow_strategy="FIFO",
    )
    interceptor.start()

    writer = MockLogWriter(source_file)
    for i in range(5):
        writer.write_line(f"Line {i}")

    time.sleep(0.3)

    lines = interceptor.get_buffered_lines()
    # Проверяем, что размер буфера не превышает максимум
    assert len(lines) == 3
    # Проверяем, что последняя строка на месте (самая важная проверка для FIFO)
    assert "Line 4\n" in lines
    # Проверяем, что первая строка была удалена
    assert "Line 0\n" not in lines

    interceptor.stop()


def test_interceptor_buffer_clear(tmp_path: Path) -> None:
    """Метод clear_buffer должен очищать буфер."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    interceptor = LogInterceptor(source_file=source_file, use_buffer=True)
    interceptor.start()

    writer = MockLogWriter(source_file)
    writer.write_line("Line 1")
    writer.write_line("Line 2")

    time.sleep(0.3)

    lines = interceptor.get_buffered_lines()
    assert len(lines) == 2

    # Очищаем буфер
    interceptor.clear_buffer()

    lines_after_clear = interceptor.get_buffered_lines()
    assert len(lines_after_clear) == 0

    interceptor.stop()


def test_interceptor_buffer_disabled(tmp_path: Path) -> None:
    """get_buffered_lines должен возвращать пустой список, если буфер не включен."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    interceptor = LogInterceptor(source_file=source_file, use_buffer=False)
    interceptor.start()

    writer = MockLogWriter(source_file)
    writer.write_line("Line 1")

    time.sleep(0.3)

    lines = interceptor.get_buffered_lines()
    assert len(lines) == 0

    interceptor.stop()
