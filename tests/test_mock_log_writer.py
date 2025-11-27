"""Тесты для MockLogWriter - mock-объекта для имитации записи логов."""

import time
from pathlib import Path

import pytest

from tests.mock_app import MockLogWriter


@pytest.mark.unit
def test_mock_log_writer_creates_file(tmp_path: Path) -> None:
    """MockLogWriter должен создать файл и записать в него строку."""
    log_file = tmp_path / "app.log"
    writer = MockLogWriter(log_file)

    writer.write_line("Test log entry")

    assert log_file.exists()
    assert log_file.read_text() == "Test log entry\n"


@pytest.mark.unit
def test_mock_log_writer_thread_mode(tmp_path: Path) -> None:
    """MockLogWriter должен работать в отдельном потоке."""
    log_file = tmp_path / "app.log"
    writer = MockLogWriter(log_file, thread_mode=True)

    writer.start()
    writer.write_line("Line 1")
    writer.write_line("Line 2")
    time.sleep(0.1)  # Даём время на запись
    writer.stop()

    lines = log_file.read_text().splitlines()
    assert len(lines) == 2
    assert lines[0] == "Line 1"
    assert lines[1] == "Line 2"
    assert not writer.is_running()


@pytest.mark.unit
def test_mock_log_writer_multiple_lines(tmp_path: Path) -> None:
    """MockLogWriter должен записывать несколько строк последовательно."""
    log_file = tmp_path / "app.log"
    writer = MockLogWriter(log_file)

    writer.write_line("Line 1")
    writer.write_line("Line 2")
    writer.write_line("Line 3")

    lines = log_file.read_text().splitlines()
    assert len(lines) == 3
    assert lines == ["Line 1", "Line 2", "Line 3"]


@pytest.mark.unit
def test_mock_log_writer_burst_mode(tmp_path: Path) -> None:
    """MockLogWriter должен поддерживать режим пакетной записи."""
    log_file = tmp_path / "app.log"
    writer = MockLogWriter(log_file)

    lines_to_write = ["Line 1", "Line 2", "Line 3"]
    writer.write_burst(lines_to_write, interval=0.01)

    # Даём время на запись
    time.sleep(0.1)

    lines = log_file.read_text().splitlines()
    assert len(lines) == 3
    assert lines == lines_to_write


@pytest.mark.unit
def test_mock_log_writer_with_delay(tmp_path: Path) -> None:
    """MockLogWriter должен поддерживать задержку при записи."""
    log_file = tmp_path / "app.log"
    writer = MockLogWriter(log_file, write_delay=0.05)

    start_time = time.time()
    writer.write_line("Test line")
    elapsed = time.time() - start_time

    # Задержка должна быть применена
    assert elapsed >= 0.05
    assert log_file.read_text() == "Test line\n"


@pytest.mark.unit
def test_mock_log_writer_rotation_scenario(tmp_path: Path) -> None:
    """MockLogWriter должен имитировать ротацию файла."""
    log_file = tmp_path / "app.log"
    writer = MockLogWriter(log_file)

    # Записываем строки до ротации
    writer.write_line("Before rotation 1")
    writer.write_line("Before rotation 2")

    # Выполняем ротацию
    rotated_file = writer.rotate_file()

    # Записываем строки после ротации
    writer.write_line("After rotation 1")
    writer.write_line("After rotation 2")

    # Проверяем старый файл (должен быть переименован)
    assert rotated_file.exists()
    old_lines = rotated_file.read_text().splitlines()
    assert len(old_lines) == 2
    assert old_lines[0] == "Before rotation 1"

    # Проверяем новый файл
    new_lines = log_file.read_text().splitlines()
    assert len(new_lines) == 2
    assert new_lines[0] == "After rotation 1"


@pytest.mark.unit
def test_mock_log_writer_context_manager(tmp_path: Path) -> None:
    """MockLogWriter должен работать как context manager в thread_mode."""
    log_file = tmp_path / "app.log"

    with MockLogWriter(log_file, thread_mode=True) as writer:
        writer.write_line("Line 1")
        writer.write_line("Line 2")
        time.sleep(0.1)

    # После выхода из контекста writer должен быть остановлен
    assert not writer.is_running()

    lines = log_file.read_text().splitlines()
    assert len(lines) == 2


@pytest.mark.unit
def test_mock_log_writer_start_without_thread_mode(tmp_path: Path) -> None:
    """start() должен вызывать ошибку если thread_mode=False."""
    log_file = tmp_path / "app.log"
    writer = MockLogWriter(log_file, thread_mode=False)

    with pytest.raises(RuntimeError, match="thread_mode=True"):
        writer.start()


@pytest.mark.unit
def test_mock_log_writer_double_start(tmp_path: Path) -> None:
    """Повторный start() должен вызывать ошибку."""
    log_file = tmp_path / "app.log"
    writer = MockLogWriter(log_file, thread_mode=True)

    writer.start()
    with pytest.raises(RuntimeError, match="is already running"):
        writer.start()

    writer.stop()


@pytest.mark.unit
def test_mock_log_writer_repr(tmp_path: Path) -> None:
    """MockLogWriter должен иметь информативный __repr__."""
    log_file = tmp_path / "app.log"
    writer = MockLogWriter(log_file, thread_mode=True)

    repr_str = repr(writer)
    assert "MockLogWriter" in repr_str
    assert "app.log" in repr_str
    assert "thread" in repr_str
    assert "stopped" in repr_str

    writer.start()
    repr_str = repr(writer)
    assert "running" in repr_str
    writer.stop()


@pytest.mark.unit
def test_mock_log_writer_get_line_count(tmp_path: Path) -> None:
    """MockLogWriter должен корректно подсчитывать количество строк."""
    log_file = tmp_path / "app.log"
    writer = MockLogWriter(log_file)

    assert writer.get_line_count() == 0

    writer.write_line("Line 1")
    assert writer.get_line_count() == 1

    writer.write_line("Line 2")
    writer.write_line("Line 3")
    assert writer.get_line_count() == 3


@pytest.mark.unit
def test_mock_log_writer_empty_burst(tmp_path: Path) -> None:
    """MockLogWriter должен корректно обрабатывать пустой список в write_burst."""
    log_file = tmp_path / "app.log"
    writer = MockLogWriter(log_file)

    writer.write_burst([])

    assert not log_file.exists() or log_file.read_text() == ""
