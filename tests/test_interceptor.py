"""Тесты для основного класса LogInterceptor."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

from log_interceptor.config import InterceptorConfig
from log_interceptor.filters import CompositeFilter, PredicateFilter, RegexFilter
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


def test_interceptor_with_filter(tmp_path: Path) -> None:
    """LogInterceptor должен применять фильтр к новым строкам."""
    source_file = tmp_path / "app.log"
    target_file = tmp_path / "captured.log"
    source_file.touch()

    error_filter = RegexFilter(r"ERROR", mode="whitelist")

    interceptor = LogInterceptor(
        source_file=source_file,
        target_file=target_file,
        filters=[error_filter],
    )
    interceptor.start()

    writer = MockLogWriter(source_file)
    writer.write_line("INFO: Application started")
    writer.write_line("ERROR: Something went wrong")
    writer.write_line("DEBUG: Debugging info")
    writer.write_line("ERROR: Another error")

    time.sleep(0.3)
    interceptor.stop()

    lines = target_file.read_text().splitlines()
    # Проверяем что все строки содержат ERROR (фильтр работает)
    assert len(lines) >= 2
    assert all("ERROR" in line for line in lines)
    # Проверяем что INFO и DEBUG отфильтрованы
    assert not any("INFO" in line for line in lines)
    assert not any("DEBUG" in line for line in lines)


def test_interceptor_with_buffer_and_filter(tmp_path: Path) -> None:
    """Фильтр должен применяться и к буферу."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    error_filter = RegexFilter(r"ERROR", mode="whitelist")

    interceptor = LogInterceptor(
        source_file=source_file,
        use_buffer=True,
        filters=[error_filter],
    )
    interceptor.start()

    writer = MockLogWriter(source_file)
    writer.write_line("INFO: Application started")
    writer.write_line("ERROR: Something went wrong")
    writer.write_line("DEBUG: Debugging info")
    writer.write_line("ERROR: Another error")

    time.sleep(0.3)

    lines = interceptor.get_buffered_lines()
    # Проверяем что все строки содержат ERROR (фильтр работает)
    assert len(lines) >= 2
    assert all("ERROR" in line for line in lines)
    # Проверяем что INFO и DEBUG отфильтрованы
    assert not any("INFO" in line for line in lines)
    assert not any("DEBUG" in line for line in lines)

    interceptor.stop()


def test_interceptor_with_multiple_filters(tmp_path: Path) -> None:
    """LogInterceptor должен применять несколько фильтров с логикой AND."""
    source_file = tmp_path / "app.log"
    target_file = tmp_path / "captured.log"
    source_file.touch()

    # Только ERROR и содержащие "critical"
    error_filter = RegexFilter(r"ERROR", mode="whitelist")
    critical_filter = PredicateFilter(lambda line: "critical" in line.lower())
    composite_filter = CompositeFilter([error_filter, critical_filter], mode="AND")

    interceptor = LogInterceptor(
        source_file=source_file,
        target_file=target_file,
        filters=[composite_filter],
    )
    interceptor.start()

    writer = MockLogWriter(source_file)
    writer.write_line("INFO: Application started")
    writer.write_line("ERROR: Something went wrong")
    writer.write_line("ERROR: Critical issue detected")
    writer.write_line("WARNING: Critical warning")

    time.sleep(0.3)
    interceptor.stop()

    lines = target_file.read_text().splitlines()
    # Должна быть минимум 1 строка
    assert len(lines) >= 1
    # Все строки должны содержать И ERROR И Critical  # noqa: RUF003
    assert all("ERROR" in line and "Critical" in line for line in lines)
    # Не должно быть INFO или WARNING  # noqa: RUF003
    assert not any("INFO" in line for line in lines)
    assert not any("WARNING" in line for line in lines)


def test_interceptor_without_filters(tmp_path: Path) -> None:
    """Без фильтров все строки должны проходить."""
    source_file = tmp_path / "app.log"
    target_file = tmp_path / "captured.log"
    source_file.touch()

    interceptor = LogInterceptor(
        source_file=source_file,
        target_file=target_file,
    )
    interceptor.start()

    writer = MockLogWriter(source_file)
    writer.write_line("Line 1")
    writer.write_line("Line 2")
    writer.write_line("Line 3")

    time.sleep(0.3)
    interceptor.stop()

    lines = target_file.read_text().splitlines()
    # Без фильтров все строки должны быть захвачены
    assert len(lines) >= 3
    assert "Line 1" in lines
    assert "Line 2" in lines
    assert "Line 3" in lines


def test_interceptor_callback_on_new_line(tmp_path: Path) -> None:
    """LogInterceptor должен вызывать callback для каждой новой строки."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    captured_lines: list[str] = []

    def on_line(line: str, _timestamp: float, _event_id: int) -> None:
        captured_lines.append(line)

    interceptor = LogInterceptor(source_file=source_file)
    interceptor.add_callback(on_line)
    interceptor.start()

    writer = MockLogWriter(source_file)
    writer.write_line("Line 1")
    writer.write_line("Line 2")

    time.sleep(0.3)
    interceptor.stop()

    assert len(captured_lines) >= 2
    assert any("Line 1" in line for line in captured_lines)
    assert any("Line 2" in line for line in captured_lines)


def test_interceptor_callback_error_handling(tmp_path: Path) -> None:
    """Ошибка в callback не должна останавливать мониторинг."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    def failing_callback(_line: str, _timestamp: float, _event_id: int) -> None:
        msg = "Callback error"
        raise ValueError(msg)

    interceptor = LogInterceptor(source_file=source_file)
    interceptor.add_callback(failing_callback)
    interceptor.start()

    writer = MockLogWriter(source_file)
    writer.write_line("Test line")

    time.sleep(0.3)

    # Interceptor всё ещё работает
    assert interceptor.is_running()

    interceptor.stop()


def test_interceptor_multiple_callbacks(tmp_path: Path) -> None:
    """LogInterceptor должен поддерживать несколько callbacks."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    captured_lines_1: list[str] = []
    captured_lines_2: list[str] = []

    def callback_1(line: str, _timestamp: float, _event_id: int) -> None:
        captured_lines_1.append(line)

    def callback_2(line: str, _timestamp: float, _event_id: int) -> None:
        captured_lines_2.append(line)

    interceptor = LogInterceptor(source_file=source_file)
    interceptor.add_callback(callback_1)
    interceptor.add_callback(callback_2)
    interceptor.start()

    writer = MockLogWriter(source_file)
    writer.write_line("Test line")

    time.sleep(0.3)
    interceptor.stop()

    # Оба callback должны быть вызваны  # noqa: RUF003
    assert len(captured_lines_1) >= 1
    assert len(captured_lines_2) >= 1


def test_interceptor_remove_callback(tmp_path: Path) -> None:
    """remove_callback должен удалять callback из списка."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    captured_lines: list[str] = []

    def on_line(line: str, _timestamp: float, _event_id: int) -> None:
        captured_lines.append(line)

    interceptor = LogInterceptor(source_file=source_file)
    interceptor.add_callback(on_line)
    interceptor.remove_callback(on_line)
    interceptor.start()

    writer = MockLogWriter(source_file)
    writer.write_line("Test line")

    time.sleep(0.3)
    interceptor.stop()

    # Callback был удален, не должен быть вызван
    assert len(captured_lines) == 0


def test_interceptor_context_manager(tmp_path: Path) -> None:
    """LogInterceptor должен поддерживать with statement."""
    source_file = tmp_path / "app.log"
    target_file = tmp_path / "captured.log"
    source_file.touch()

    with LogInterceptor(source_file=source_file, target_file=target_file) as interceptor:
        assert interceptor.is_running()

        writer = MockLogWriter(source_file)
        writer.write_line("Test line")
        time.sleep(0.3)

    # После выхода из контекста должен быть остановлен
    assert not interceptor.is_running()
    assert target_file.exists()


def test_interceptor_context_manager_cleanup_on_exception(tmp_path: Path) -> None:
    """LogInterceptor должен освобождать ресурсы даже при исключении."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    interceptor = None
    try:
        with LogInterceptor(source_file=source_file) as interceptor:
            assert interceptor.is_running()
            msg = "Test exception"
            raise RuntimeError(msg)
    except RuntimeError:
        pass

    assert interceptor is not None
    assert not interceptor.is_running()


def test_interceptor_handles_missing_file(tmp_path: Path) -> None:
    """LogInterceptor должен обрабатывать временную недоступность файла."""
    source_file = tmp_path / "app.log"

    # Файл ещё не существует
    interceptor = LogInterceptor(source_file=source_file, allow_missing=True, use_buffer=True)
    interceptor.start()

    # Файл появляется
    time.sleep(0.2)
    source_file.write_text("First line\n")

    time.sleep(0.5)

    # Добавляем новую строку
    source_file.write_text("First line\nSecond line\n")
    time.sleep(0.3)

    lines = interceptor.get_buffered_lines()
    interceptor.stop()

    # Должна быть захвачена хотя бы "Second line"
    assert len(lines) >= 1
    assert any("Second line" in line for line in lines)


def test_interceptor_handles_permission_error(tmp_path: Path) -> None:
    """LogInterceptor должен обрабатывать PermissionError."""
    source_file = tmp_path / "app.log"
    source_file.write_text("Initial\n")

    interceptor = LogInterceptor(source_file=source_file, use_buffer=True)
    interceptor.start()

    # Имитируем потерю прав доступа
    source_file.chmod(0o000)

    time.sleep(0.3)

    # LogInterceptor должен продолжать работать
    assert interceptor.is_running()

    # Восстанавливаем права
    source_file.chmod(0o644)

    interceptor.stop()


def test_interceptor_handles_file_rotation(tmp_path: Path) -> None:
    """LogInterceptor должен обрабатывать ротацию лог-файла."""
    source_file = tmp_path / "app.log"
    source_file.write_text("Initial\n")

    interceptor = LogInterceptor(source_file=source_file, use_buffer=True)
    interceptor.start()

    writer = MockLogWriter(source_file)
    writer.write_line("Line before rotation")
    time.sleep(0.3)

    # Ротация: переименовываем старый файл, создаём новый
    rotated_file = tmp_path / "app.log.1"
    source_file.rename(rotated_file)
    source_file.write_text("")  # Новый файл

    writer = MockLogWriter(source_file)
    writer.write_line("Line after rotation")
    time.sleep(0.5)

    lines = interceptor.get_buffered_lines()
    interceptor.stop()

    # Должны быть обе строки  # noqa: RUF003
    assert any("Line before rotation" in line for line in lines)
    assert any("Line after rotation" in line for line in lines)


def test_interceptor_with_config(tmp_path: Path) -> None:
    """LogInterceptor должен использовать настройки из InterceptorConfig."""
    source_file = tmp_path / "app.log"
    target_file = tmp_path / "captured.log"
    source_file.touch()

    # Создаём кастомную конфигурацию
    config = InterceptorConfig(
        encoding="utf-8",
        buffer_size=500,
        debounce_interval=0.05,
    )

    interceptor = LogInterceptor(
        source_file=source_file,
        target_file=target_file,
        use_buffer=True,
        config=config,
    )
    interceptor.start()

    writer = MockLogWriter(source_file)
    writer.write_line("Test with config")

    time.sleep(0.3)
    interceptor.stop()

    # Проверяем что файл был записан с правильной кодировкой  # noqa: RUF003
    content = target_file.read_text(encoding="utf-8")
    assert "Test with config" in content


def test_interceptor_adds_timestamps(tmp_path: Path) -> None:
    """LogInterceptor должен добавлять timestamp к захваченным строкам."""
    source_file = tmp_path / "app.log"
    target_file = tmp_path / "captured.log"
    source_file.touch()

    interceptor = LogInterceptor(
        source_file=source_file,
        target_file=target_file,
        add_timestamps=True,
    )
    interceptor.start()

    writer = MockLogWriter(source_file)
    writer.write_line("Test line")
    time.sleep(0.3)

    interceptor.stop()

    content = target_file.read_text()
    # Формат: [CAPTURED_AT: 2025-11-27T10:30:45.123456] Test line
    assert "[CAPTURED_AT:" in content
    assert "Test line" in content


def test_interceptor_get_lines_with_metadata(tmp_path: Path) -> None:
    """LogInterceptor должен возвращать строки с метаданными."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    interceptor = LogInterceptor(source_file=source_file, use_buffer=True)
    interceptor.start()

    writer = MockLogWriter(source_file)
    writer.write_line("Test")
    time.sleep(0.3)

    lines_with_meta = interceptor.get_lines_with_metadata()
    interceptor.stop()

    assert len(lines_with_meta) >= 1
    entry = lines_with_meta[0]
    assert "line" in entry
    assert "timestamp" in entry
    assert "event_id" in entry
    assert entry["line"] == "Test"
    assert isinstance(entry["timestamp"], float)
    assert isinstance(entry["event_id"], int)


def test_interceptor_pause_resume(tmp_path: Path) -> None:
    """LogInterceptor должен поддерживать pause/resume."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    interceptor = LogInterceptor(source_file=source_file, use_buffer=True)
    interceptor.start()

    writer = MockLogWriter(source_file)
    writer.write_line("Line 1")
    time.sleep(0.3)

    interceptor.pause()
    assert interceptor.is_paused()

    # Строки во время паузы не должны захватываться
    writer.write_line("Line during pause")
    time.sleep(0.3)

    interceptor.resume()
    assert not interceptor.is_paused()

    writer.write_line("Line 2")
    time.sleep(0.3)

    lines = interceptor.get_buffered_lines()
    interceptor.stop()

    # Line 1 и Line 2 должны быть захвачены
    assert any("Line 1" in line for line in lines)
    assert any("Line 2" in line for line in lines)
    # Line during pause НЕ должна быть захвачена  # noqa: RUF003
    assert not any("Line during pause" in line for line in lines)


def test_interceptor_statistics(tmp_path: Path) -> None:
    """LogInterceptor должен собирать статистику."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    interceptor = LogInterceptor(source_file=source_file, use_buffer=True)
    interceptor.start()

    writer = MockLogWriter(source_file)
    writer.write_line("Line 1")
    writer.write_line("Line 2")
    writer.write_line("Line 3")
    time.sleep(0.3)

    stats = interceptor.get_stats()
    interceptor.stop()

    assert stats["lines_captured"] >= 3
    assert stats["events_processed"] >= 1
    assert "start_time" in stats
    assert "uptime_seconds" in stats
    assert isinstance(stats["start_time"], float)
    assert isinstance(stats["uptime_seconds"], float)
    assert stats["uptime_seconds"] > 0


def test_interceptor_debounce_prevents_duplicates(tmp_path: Path) -> None:
    """Debounce должен предотвращать обработку дублирующихся событий."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    config = InterceptorConfig(debounce_interval=0.5)
    interceptor = LogInterceptor(
        source_file=source_file,
        config=config,
        use_buffer=True,
    )
    interceptor.start()

    # Быстрые множественные записи
    writer = MockLogWriter(source_file)
    for i in range(10):
        writer.write_line(f"Line {i}")
        time.sleep(0.05)  # Быстрее чем debounce (0.5s)

    time.sleep(1.0)  # Ждём завершения debounce

    stats = interceptor.get_stats()
    interceptor.stop()

    # Должно быть обработано меньше событий из-за debounce
    assert stats["events_processed"] < 10
    # Но все строки должны быть захвачены  # noqa: RUF003
    lines = interceptor.get_buffered_lines()
    assert len(lines) >= 10
