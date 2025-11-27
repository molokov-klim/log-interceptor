"""Интеграционные тесты LogInterceptor.

Тесты реальных сценариев использования библиотеки.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from log_interceptor.filters import RegexFilter
from log_interceptor.interceptor import LogInterceptor
from tests.mock_app import MockLogWriter

if TYPE_CHECKING:
    from pathlib import Path


def test_integration_basic_usage(log_interceptor: LogInterceptor) -> None:
    """Базовый сценарий использования: захват логов в буфер."""
    log_interceptor.start()

    # Создаем writer и пишем логи
    writer = MockLogWriter(log_interceptor.source_file)
    writer.write_line("Application started")
    writer.write_line("Processing request...")
    writer.write_line("Request completed")

    time.sleep(0.3)
    log_interceptor.stop()

    lines = log_interceptor.get_buffered_lines()
    assert len(lines) >= 3
    assert any("Application started" in line for line in lines)
    assert any("Request completed" in line for line in lines)


def test_integration_with_filter_and_callback(tmp_path: Path) -> None:
    """Сценарий с фильтром и callback: захват только ERROR строк."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    # Счетчик для callback
    error_count = 0

    def on_error(_line: str, _timestamp: float, _event_id: int) -> None:
        nonlocal error_count
        error_count += 1

    # Создаем interceptor с фильтром на ERROR
    error_filter = RegexFilter(r"ERROR", mode="whitelist")
    interceptor = LogInterceptor(
        source_file=source_file,
        use_buffer=True,
        filters=[error_filter],
    )
    interceptor.add_callback(on_error)
    interceptor.start()

    # Пишем логи разных уровней
    writer = MockLogWriter(source_file)
    writer.write_line("INFO: Application started")
    writer.write_line("ERROR: Failed to connect")
    writer.write_line("DEBUG: Processing...")
    writer.write_line("ERROR: Timeout occurred")
    writer.write_line("INFO: Shutting down")

    time.sleep(0.3)
    interceptor.stop()

    # Проверяем что захвачены только ERROR
    lines = interceptor.get_buffered_lines()
    assert len(lines) >= 2
    assert all("ERROR" in line for line in lines)
    assert error_count >= 2


def test_integration_context_manager_with_stats(tmp_path: Path) -> None:
    """Сценарий с context manager и получением статистики."""
    source_file = tmp_path / "app.log"
    target_file = tmp_path / "captured.log"
    source_file.touch()

    with LogInterceptor(
        source_file=source_file,
        target_file=target_file,
        use_buffer=True,
    ) as interceptor:
        # Пишем логи
        writer = MockLogWriter(source_file)
        for i in range(10):
            writer.write_line(f"Log entry {i}")

        time.sleep(0.3)

        # Получаем статистику во время работы
        stats = interceptor.get_stats()
        assert stats["lines_captured"] >= 10
        assert stats["uptime_seconds"] > 0

    # После выхода interceptor автоматически остановлен
    assert not interceptor.is_running()
    assert target_file.exists()


def test_integration_pause_resume_workflow(tmp_path: Path) -> None:
    """Сценарий с pause/resume для контроля потока данных."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    interceptor = LogInterceptor(source_file=source_file, use_buffer=True)
    interceptor.start()

    writer = MockLogWriter(source_file)

    # Фаза 1: Нормальный захват
    writer.write_line("Phase 1: Normal operation")
    time.sleep(0.2)

    # Пауза для обработки
    interceptor.pause()
    assert interceptor.is_paused()

    # Обрабатываем буфер (в реальном приложении - сохранение в БД и т.д.)
    buffered = interceptor.get_buffered_lines()
    assert len(buffered) >= 1

    # Очищаем буфер после обработки
    interceptor.clear_buffer()

    # Пишем во время паузы - эти данные не должны захватываться
    writer.write_line("Phase 2: During pause - should be skipped")
    time.sleep(0.2)

    # Возобновляем захват
    interceptor.resume()
    assert not interceptor.is_paused()

    # Фаза 3: Захват возобновлен
    writer.write_line("Phase 3: Resumed operation")
    time.sleep(0.2)

    lines = interceptor.get_buffered_lines()
    interceptor.stop()

    # Проверяем что Phase 2 не захвачена
    assert any("Phase 3" in line for line in lines)
    assert not any("Phase 2" in line for line in lines)


def test_integration_metadata_tracking(tmp_path: Path) -> None:
    """Сценарий с отслеживанием метаданных для аудита."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    interceptor = LogInterceptor(source_file=source_file, use_buffer=True)
    interceptor.start()

    writer = MockLogWriter(source_file)
    writer.write_line("Transaction started")
    writer.write_line("Payment processed")
    writer.write_line("Transaction completed")

    time.sleep(0.3)

    # Получаем метаданные для аудита
    metadata = interceptor.get_lines_with_metadata()
    interceptor.stop()

    assert len(metadata) >= 3

    # Проверяем структуру метаданных
    for entry in metadata:
        assert "line" in entry
        assert "timestamp" in entry
        assert "event_id" in entry
        assert isinstance(entry["timestamp"], float)
        assert isinstance(entry["event_id"], int)

    # Проверяем что event_id уникальны и последовательны
    event_ids = [entry["event_id"] for entry in metadata]
    assert len(event_ids) == len(set(event_ids))  # Все уникальны


def test_integration_error_recovery(tmp_path: Path) -> None:
    """Сценарий с обработкой ошибок: ротация файла."""
    source_file = tmp_path / "app.log"
    source_file.write_text("Initial content\n")

    interceptor = LogInterceptor(source_file=source_file, use_buffer=True)
    interceptor.start()

    writer = MockLogWriter(source_file)
    writer.write_line("Before rotation")
    time.sleep(0.3)

    # Имитируем ротацию файла
    rotated = tmp_path / "app.log.1"
    source_file.rename(rotated)
    source_file.write_text("")  # Новый файл

    writer = MockLogWriter(source_file)
    writer.write_line("After rotation")
    time.sleep(0.3)

    lines = interceptor.get_buffered_lines()
    interceptor.stop()

    # Должны быть захвачены обе строки
    assert any("Before rotation" in line for line in lines)
    assert any("After rotation" in line for line in lines)

