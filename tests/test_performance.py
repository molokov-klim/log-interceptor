"""Тесты производительности для LogInterceptor.

Используют pytest-benchmark для измерения производительности.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

import pytest

from log_interceptor.config import InterceptorConfig
from log_interceptor.filters import RegexFilter
from log_interceptor.interceptor import LogInterceptor
from tests.mock_app import MockLogWriter

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_benchmark.fixture import BenchmarkFixture


def test_interceptor_performance_high_volume(tmp_path: Path, benchmark: BenchmarkFixture) -> None:
    """LogInterceptor должен эффективно обрабатывать большие объёмы данных."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    interceptor = LogInterceptor(source_file=source_file, use_buffer=True, buffer_size=5000)

    def write_1000_lines() -> None:
        writer = MockLogWriter(source_file)
        lines = [f"Line {i}\n" for i in range(1000)]
        writer.write_burst(lines, interval=0.001)

    interceptor.start()

    # Benchmark только запись
    benchmark(write_1000_lines)

    time.sleep(1.5)  # Даем время на обработку

    stats = interceptor.get_stats()
    interceptor.stop()

    # Проверяем что все строки захвачены
    # Примечание: может быть больше из-за множественных rounds бенчмарка
    assert stats["lines_captured"] >= 1000, f"Expected >= 1000, got {stats['lines_captured']}"


def test_interceptor_performance_with_filter(tmp_path: Path, benchmark: BenchmarkFixture) -> None:
    """Проверка производительности с фильтрацией."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    # Фильтр только на ERROR
    error_filter = RegexFilter(r"ERROR", mode="whitelist")
    interceptor = LogInterceptor(
        source_file=source_file,
        filters=[error_filter],
        use_buffer=True,
        buffer_size=5000,
    )

    def write_mixed_lines() -> None:
        writer = MockLogWriter(source_file)
        lines = []
        for i in range(1000):
            if i % 10 == 0:
                lines.append(f"ERROR: Error {i}\n")
            else:
                lines.append(f"INFO: Info {i}\n")
        writer.write_burst(lines, interval=0.001)

    interceptor.start()
    benchmark(write_mixed_lines)
    time.sleep(1.5)

    stats = interceptor.get_stats()
    interceptor.stop()

    # Должно быть захвачено ~100 ERROR строк (может быть больше из-за rounds)
    assert stats["lines_captured"] >= 90, f"Expected >= 90, got {stats['lines_captured']}"


def test_interceptor_performance_debounce(tmp_path: Path, benchmark: BenchmarkFixture) -> None:
    """Проверка производительности debounce механизма."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    # Короткий debounce интервал
    config = InterceptorConfig(debounce_interval=0.01)
    interceptor = LogInterceptor(
        source_file=source_file,
        config=config,
        use_buffer=True,
        buffer_size=5000,
    )

    def write_rapid_lines() -> None:
        writer = MockLogWriter(source_file)
        lines = [f"Line {i}\n" for i in range(500)]
        writer.write_burst(lines, interval=0.001)  # Очень быстро

    interceptor.start()
    benchmark(write_rapid_lines)
    time.sleep(1.0)

    stats = interceptor.get_stats()
    interceptor.stop()

    # Все строки должны быть захвачены (может быть больше из-за rounds)
    assert stats["lines_captured"] >= 500
    # events_processed может быть меньше из-за debounce
    # но с множественными rounds может быть больше 500
    assert stats["events_processed"] >= 1


def test_interceptor_performance_buffer_operations(tmp_path: Path, benchmark: BenchmarkFixture) -> None:
    """Проверка производительности операций с буфером."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    interceptor = LogInterceptor(source_file=source_file, use_buffer=True, buffer_size=10000)
    interceptor.start()

    # Записываем данные
    writer = MockLogWriter(source_file)
    lines = [f"Line {i}\n" for i in range(5000)]
    writer.write_burst(lines, interval=0.0001)
    time.sleep(2.0)

    # Benchmark операций чтения буфера
    def read_buffer() -> list[str]:
        return interceptor.get_buffered_lines()

    result = benchmark(read_buffer)
    interceptor.stop()

    # Проверяем что буфер не пуст
    assert len(result) > 0


def test_interceptor_performance_metadata(tmp_path: Path, benchmark: BenchmarkFixture) -> None:
    """Проверка производительности операций с метаданными."""
    source_file = tmp_path / "app.log"
    source_file.touch()

    interceptor = LogInterceptor(source_file=source_file, use_buffer=True, buffer_size=10000)
    interceptor.start()

    # Записываем данные
    writer = MockLogWriter(source_file)
    lines = [f"Line {i}\n" for i in range(2000)]
    writer.write_burst(lines, interval=0.0001)
    time.sleep(2.0)

    # Benchmark операций чтения метаданных
    def read_metadata() -> list:
        return interceptor.get_lines_with_metadata()

    result = benchmark(read_metadata)
    interceptor.stop()

    # Проверяем что метаданные есть
    assert len(result) > 0


@pytest.mark.slow
def test_interceptor_large_file_handling(tmp_path: Path) -> None:
    """Тест обработки очень больших файлов (отмечен как slow)."""
    source_file = tmp_path / "large.log"
    source_file.touch()

    interceptor = LogInterceptor(source_file=source_file, use_buffer=True, buffer_size=50000)
    interceptor.start()

    # Записываем 50000 строк
    writer = MockLogWriter(source_file)
    lines = [f"Line {i}\n" for i in range(50000)]
    writer.write_burst(lines, interval=0.00001)

    # Даем достаточно времени на обработку
    time.sleep(10.0)

    stats = interceptor.get_stats()
    interceptor.stop()

    # Проверяем что большая часть строк захвачена
    assert stats["lines_captured"] >= 40000, f"Expected >= 40000, got {stats['lines_captured']}"

    # Проверяем производительность
    uptime = stats["uptime_seconds"]
    lines_per_second = stats["lines_captured"] / uptime if uptime > 0 else 0

    # Должно обрабатывать хотя бы 1000 строк в секунду
    assert lines_per_second >= 1000, f"Too slow: {lines_per_second:.2f} lines/sec"

