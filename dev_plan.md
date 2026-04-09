# План разработки LogInterceptor (TDD подход)

## Обзор

Этот документ описывает пошаговый план разработки библиотеки **LogInterceptor** с использованием методологии **Test-Driven Development (TDD)**. Каждая итерация следует циклу: **Red → Green → Refactor**.

---

## Подготовительный этап

### Этап 0: Инфраструктура проекта

#### Задачи:
1. ✅ Создать структуру проекта
2. Настроить `pyproject.toml` с зависимостями
3. Настроить линтеры (ruff, pyright)
4. Настроить GitHub Actions для CI/CD
5. Создать базовый README.md

#### Зависимости:
```toml
dependencies = [
    "watchdog>=3.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "pyright>=1.1.0",
]
```

---

## Итерация 1: MockLogWriter и базовая инфраструктура тестов

### Цель:
Создать mock-объект для имитации внешнего приложения, записывающего логи. Это фундамент для всех последующих тестов.

### TDD Цикл 1.1: MockLogWriter - базовая запись

#### RED: Написать тест
```python
# tests/test_mock_log_writer.py
def test_mock_log_writer_creates_file(tmp_path):
    """MockLogWriter должен создать файл и записать в него строку"""
    log_file = tmp_path / "app.log"
    writer = MockLogWriter(log_file)
    
    writer.write_line("Test log entry")
    
    assert log_file.exists()
    assert log_file.read_text() == "Test log entry\n"
```

#### GREEN: Реализовать минимальный код
```python
# tests/mock_app.py
class MockLogWriter:
    def __init__(self, log_file_path):
        self.log_file = Path(log_file_path)
    
    def write_line(self, line):
        with open(self.log_file, 'a') as f:
            f.write(f"{line}\n")
```

#### REFACTOR: Улучшить при необходимости

### TDD Цикл 1.2: MockLogWriter - работа в потоке

#### RED: Тест для асинхронной записи
```python
def test_mock_log_writer_thread_mode(tmp_path):
    """MockLogWriter должен работать в отдельном потоке"""
    log_file = tmp_path / "app.log"
    writer = MockLogWriter(log_file, thread_mode=True)
    
    writer.start()
    writer.write_line("Line 1")
    writer.write_line("Line 2")
    time.sleep(0.1)  # Даём время на запись
    writer.stop()
    
    lines = log_file.read_text().splitlines()
    assert len(lines) == 2
    assert not writer.is_running()
```

#### GREEN: Реализация потоковой модели

### TDD Цикл 1.3: MockLogWriter - контролируемые сценарии

#### RED: Тесты для различных сценариев
```python
def test_mock_log_writer_burst_mode(tmp_path):
    """MockLogWriter должен поддерживать режим пачечной записи"""
    writer = MockLogWriter(tmp_path / "app.log")
    writer.write_burst(["Line 1", "Line 2", "Line 3"], interval=0.01)
    # ...

def test_mock_log_writer_slow_mode(tmp_path):
    """MockLogWriter должен поддерживать медленную запись"""
    writer = MockLogWriter(tmp_path / "app.log", write_delay=0.5)
    # ...

def test_mock_log_writer_rotation_scenario(tmp_path):
    """MockLogWriter должен имитировать ротацию файла"""
    writer = MockLogWriter(tmp_path / "app.log")
    writer.rotate_file()  # Переименовать старый, создать новый
    # ...
```

#### GREEN: Реализация сценариев

### Deliverables:
- ✅ `tests/mock_app.py` с классом `MockLogWriter`
- ✅ `tests/test_mock_log_writer.py` с полным покрытием

---

## Итерация 2: Базовые исключения и конфигурация

### TDD Цикл 2.1: Пользовательские исключения

#### RED: Тесты исключений
```python
# tests/test_exceptions.py
def test_interceptor_error_hierarchy():
    """Все исключения должны наследоваться от LogInterceptorError"""
    assert issubclass(FileWatchError, LogInterceptorError)
    assert issubclass(FilterError, LogInterceptorError)
    # ...
```

#### GREEN: Реализация
```python
# log_interceptor/exceptions.py
class LogInterceptorError(Exception):
    """Базовое исключение"""
    pass

class FileWatchError(LogInterceptorError):
    """Ошибка при мониторинге файла"""
    pass

class FilterError(LogInterceptorError):
    """Ошибка при фильтрации логов"""
    pass
```

### TDD Цикл 2.2: Класс конфигурации

#### RED: Тесты конфигурации
```python
# tests/test_config.py
def test_config_default_values():
    """Config должен иметь разумные значения по умолчанию"""
    config = InterceptorConfig()
    assert config.debounce_interval == 0.1
    assert config.buffer_size == 1000
    # ...

def test_config_presets():
    """Config должен поддерживать предустановки"""
    config = InterceptorConfig.from_preset("aggressive")
    assert config.debounce_interval == 0.01
    # ...
```

#### GREEN: Реализация
```python
# log_interceptor/config.py
@dataclass
class InterceptorConfig:
    debounce_interval: float = 0.1
    buffer_size: int = 1000
    # ...
    
    @classmethod
    def from_preset(cls, preset: str):
        # ...
```

### Deliverables:
- ✅ `log_interceptor/exceptions.py`
- ✅ `log_interceptor/config.py`
- ✅ Тесты для обоих модулей

---

## Итерация 3: Система фильтров

### TDD Цикл 3.1: Базовый интерфейс фильтра

#### RED: Тест базового фильтра
```python
# tests/test_filters.py
def test_base_filter_interface():
    """Все фильтры должны реализовывать метод filter()"""
    class CustomFilter(BaseFilter):
        def filter(self, line: str) -> bool:
            return True
    
    f = CustomFilter()
    assert f.filter("test") is True
```

#### GREEN: Реализация
```python
# log_interceptor/filters.py
from abc import ABC, abstractmethod

class BaseFilter(ABC):
    @abstractmethod
    def filter(self, line: str) -> bool:
        """Возвращает True, если строка должна быть включена"""
        pass
```

### TDD Цикл 3.2: RegexFilter

#### RED: Тесты для RegexFilter
```python
def test_regex_filter_match():
    """RegexFilter должен фильтровать по регулярному выражению"""
    filter = RegexFilter(r"ERROR.*")
    assert filter.filter("ERROR: Something went wrong") is True
    assert filter.filter("INFO: All good") is False

def test_regex_filter_whitelist():
    """RegexFilter с режимом whitelist должен включать только совпадения"""
    filter = RegexFilter(r"^ERROR", mode="whitelist")
    assert filter.filter("ERROR: test") is True
    assert filter.filter("INFO: test") is False

def test_regex_filter_blacklist():
    """RegexFilter с режимом blacklist должен исключать совпадения"""
    filter = RegexFilter(r"^DEBUG", mode="blacklist")
    assert filter.filter("DEBUG: test") is False
    assert filter.filter("ERROR: test") is True
```

#### GREEN: Реализация RegexFilter

### TDD Цикл 3.3: PredicateFilter и CompositeFilter

#### RED: Тесты
```python
def test_predicate_filter():
    """PredicateFilter должен использовать пользовательскую функцию"""
    filter = PredicateFilter(lambda line: len(line) > 10)
    assert filter.filter("short") is False
    assert filter.filter("this is a longer line") is True

def test_composite_filter_and():
    """CompositeFilter должен поддерживать логику AND"""
    f1 = RegexFilter(r"ERROR")
    f2 = PredicateFilter(lambda x: len(x) > 20)
    composite = CompositeFilter([f1, f2], mode="AND")
    
    assert composite.filter("ERROR: x") is False  # f2 не пройден
    assert composite.filter("ERROR: this is a very long message") is True

def test_composite_filter_or():
    """CompositeFilter должен поддерживать логику OR"""
    f1 = RegexFilter(r"ERROR")
    f2 = RegexFilter(r"CRITICAL")
    composite = CompositeFilter([f1, f2], mode="OR")
    
    assert composite.filter("ERROR: test") is True
    assert composite.filter("CRITICAL: test") is True
    assert composite.filter("INFO: test") is False
```

#### GREEN: Реализация фильтров

### Deliverables:
- ✅ `log_interceptor/filters.py` с классами:
  - `BaseFilter`
  - `RegexFilter`
  - `PredicateFilter`
  - `CompositeFilter`
- ✅ Полное покрытие тестами

---

## Итерация 4: Ядро LogInterceptor - базовый мониторинг

### TDD Цикл 4.1: Инициализация и базовые методы

#### RED: Тесты инициализации
```python
# tests/test_interceptor.py
def test_interceptor_initialization(tmp_path):
    """LogInterceptor должен инициализироваться с путём к файлу"""
    log_file = tmp_path / "app.log"
    log_file.touch()
    
    interceptor = LogInterceptor(source_file=log_file)
    
    assert interceptor.source_file == log_file
    assert not interceptor.is_running()

def test_interceptor_requires_existing_file(tmp_path):
    """LogInterceptor должен требовать существующий файл или allow_missing=True"""
    non_existent = tmp_path / "missing.log"
    
    with pytest.raises(FileNotFoundError):
        LogInterceptor(source_file=non_existent)
    
    # Должно работать с флагом
    interceptor = LogInterceptor(source_file=non_existent, allow_missing=True)
    assert interceptor is not None
```

#### GREEN: Базовая реализация
```python
# log_interceptor/interceptor.py
class LogInterceptor:
    def __init__(self, source_file, allow_missing=False):
        self.source_file = Path(source_file)
        if not allow_missing and not self.source_file.exists():
            raise FileNotFoundError(f"Source file not found: {source_file}")
        self._running = False
    
    def is_running(self):
        return self._running
```

### TDD Цикл 4.2: Start/Stop механика

#### RED: Тесты запуска/остановки
```python
def test_interceptor_start_stop(tmp_path):
    """LogInterceptor должен корректно запускаться и останавливаться"""
    log_file = tmp_path / "app.log"
    log_file.touch()
    
    interceptor = LogInterceptor(source_file=log_file)
    
    interceptor.start()
    assert interceptor.is_running()
    
    interceptor.stop()
    assert not interceptor.is_running()

def test_interceptor_double_start_raises(tmp_path):
    """Повторный start() должен вызывать исключение"""
    log_file = tmp_path / "app.log"
    log_file.touch()
    
    interceptor = LogInterceptor(source_file=log_file)
    interceptor.start()
    
    with pytest.raises(RuntimeError):
        interceptor.start()
    
    interceptor.stop()
```

#### GREEN: Реализация start/stop

### TDD Цикл 4.3: Захват новых строк в файл

#### RED: Тест захвата логов
```python
def test_interceptor_captures_new_lines(tmp_path):
    """LogInterceptor должен захватывать новые строки из файла"""
    source_file = tmp_path / "app.log"
    target_file = tmp_path / "captured.log"
    
    # Создаём исходный файл с начальным содержимым
    source_file.write_text("Initial line\n")
    
    interceptor = LogInterceptor(
        source_file=source_file,
        target_file=target_file
    )
    interceptor.start()
    
    # MockLogWriter добавляет новые строки
    writer = MockLogWriter(source_file, append=True)
    writer.write_line("New line 1")
    writer.write_line("New line 2")
    
    # Даём время на обработку
    time.sleep(0.5)
    
    interceptor.stop()
    
    # Проверяем захваченные строки
    captured = target_file.read_text().splitlines()
    assert "New line 1" in captured
    assert "New line 2" in captured
    assert "Initial line" not in captured  # Не должен захватывать старые
```

#### GREEN: Реализация watchdog observer

### Deliverables:
- ✅ `log_interceptor/interceptor.py` с классом `LogInterceptor`
- ✅ Базовый мониторинг файлов через watchdog
- ✅ Захват новых строк в target_file

---

## Итерация 5: Буферизация в памяти

### TDD Цикл 5.1: In-memory buffer

#### RED: Тесты буфера
```python
def test_interceptor_memory_buffer(tmp_path):
    """LogInterceptor должен хранить строки в памяти"""
    source_file = tmp_path / "app.log"
    source_file.write_text("Old line\n")
    
    interceptor = LogInterceptor(
        source_file=source_file,
        use_buffer=True,
        buffer_size=100
    )
    interceptor.start()
    
    writer = MockLogWriter(source_file, append=True)
    writer.write_line("Line 1")
    writer.write_line("Line 2")
    
    time.sleep(0.3)
    
    lines = interceptor.get_buffered_lines()
    assert len(lines) >= 2
    assert "Line 1" in lines
    assert "Line 2" in lines
    
    interceptor.stop()

def test_interceptor_buffer_overflow_fifo(tmp_path):
    """Буфер должен удалять старые строки при переполнении (FIFO)"""
    source_file = tmp_path / "app.log"
    source_file.touch()
    
    interceptor = LogInterceptor(
        source_file=source_file,
        use_buffer=True,
        buffer_size=3,
        overflow_strategy="FIFO"
    )
    interceptor.start()
    
    writer = MockLogWriter(source_file)
    for i in range(5):
        writer.write_line(f"Line {i}")
    
    time.sleep(0.3)
    
    lines = interceptor.get_buffered_lines()
    assert len(lines) == 3
    assert "Line 2" in lines
    assert "Line 3" in lines
    assert "Line 4" in lines
    assert "Line 0" not in lines
    
    interceptor.stop()
```

#### GREEN: Реализация буфера
```python
# log_interceptor/interceptor.py
from collections import deque
import threading

class LogInterceptor:
    def __init__(self, ..., use_buffer=False, buffer_size=1000, overflow_strategy="FIFO"):
        # ...
        self._buffer = deque(maxlen=buffer_size) if use_buffer else None
        self._buffer_lock = threading.Lock()
    
    def get_buffered_lines(self):
        if not self._buffer:
            return []
        with self._buffer_lock:
            return list(self._buffer)
```

### Deliverables:
- ✅ In-memory буферизация
- ✅ Стратегии переполнения
- ✅ Потокобезопасный доступ

---

## Итерация 6: Интеграция фильтров

### TDD Цикл 6.1: Применение фильтров к строкам

#### RED: Тесты фильтрации
```python
def test_interceptor_with_filter(tmp_path):
    """LogInterceptor должен применять фильтр к новым строкам"""
    source_file = tmp_path / "app.log"
    target_file = tmp_path / "captured.log"
    source_file.touch()
    
    error_filter = RegexFilter(r"ERROR", mode="whitelist")
    
    interceptor = LogInterceptor(
        source_file=source_file,
        target_file=target_file,
        filters=[error_filter]
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
    assert len(lines) == 2
    assert all("ERROR" in line for line in lines)
```

#### GREEN: Интеграция фильтров в LogInterceptor

### Deliverables:
- ✅ Применение фильтров при захвате
- ✅ Поддержка множественных фильтров

---

## Итерация 7: Callback система

### TDD Цикл 7.1: Регистрация и вызов callbacks

#### RED: Тесты callbacks
```python
def test_interceptor_callback_on_new_line(tmp_path):
    """LogInterceptor должен вызывать callback для каждой новой строки"""
    source_file = tmp_path / "app.log"
    source_file.touch()
    
    captured_lines = []
    
    def on_line(line, timestamp, event_id):
        captured_lines.append(line)
    
    interceptor = LogInterceptor(source_file=source_file)
    interceptor.add_callback(on_line)
    interceptor.start()
    
    writer = MockLogWriter(source_file)
    writer.write_line("Line 1")
    writer.write_line("Line 2")
    
    time.sleep(0.3)
    interceptor.stop()
    
    assert len(captured_lines) == 2
    assert "Line 1" in captured_lines
    assert "Line 2" in captured_lines

def test_interceptor_callback_error_handling(tmp_path):
    """Ошибка в callback не должна останавливать мониторинг"""
    source_file = tmp_path / "app.log"
    source_file.touch()
    
    def failing_callback(line, timestamp, event_id):
        raise ValueError("Callback error")
    
    interceptor = LogInterceptor(source_file=source_file)
    interceptor.add_callback(failing_callback)
    interceptor.start()
    
    writer = MockLogWriter(source_file)
    writer.write_line("Test line")
    
    time.sleep(0.3)
    
    # Interceptor всё ещё работает
    assert interceptor.is_running()
    
    interceptor.stop()
```

#### GREEN: Реализация callback системы

### Deliverables:
- ✅ Регистрация callbacks
- ✅ Асинхронное выполнение
- ✅ Обработка ошибок в callbacks

---

## Итерация 8: Context Manager

### TDD Цикл 8.1: With statement support

#### RED: Тесты контекстного менеджера
```python
def test_interceptor_context_manager(tmp_path):
    """LogInterceptor должен поддерживать with statement"""
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

def test_interceptor_context_manager_cleanup_on_exception(tmp_path):
    """LogInterceptor должен освобождать ресурсы даже при исключении"""
    source_file = tmp_path / "app.log"
    source_file.touch()
    
    try:
        with LogInterceptor(source_file=source_file) as interceptor:
            assert interceptor.is_running()
            raise RuntimeError("Test exception")
    except RuntimeError:
        pass
    
    assert not interceptor.is_running()
```

#### GREEN: Реализация __enter__ и __exit__

### Deliverables:
- ✅ Context manager support
- ✅ Гарантированная очистка ресурсов

---

## Итерация 9: Обработка ошибок и восстановление

### TDD Цикл 9.1: Обработка недоступности файла

#### RED: Тесты обработки ошибок
```python
def test_interceptor_handles_missing_file(tmp_path):
    """LogInterceptor должен обрабатывать временную недоступность файла"""
    source_file = tmp_path / "app.log"
    
    # Файл ещё не существует
    interceptor = LogInterceptor(source_file=source_file, allow_missing=True)
    interceptor.start()
    
    # Файл появляется
    time.sleep(0.2)
    source_file.write_text("First line\n")
    
    time.sleep(0.5)
    
    # Должен начать отслеживание
    source_file.write_text("First line\nSecond line\n")
    time.sleep(0.3)
    
    lines = interceptor.get_buffered_lines() if interceptor._buffer else []
    interceptor.stop()

def test_interceptor_handles_permission_error(tmp_path):
    """LogInterceptor должен обрабатывать PermissionError"""
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
```

#### GREEN: Реализация обработки ошибок с retry и exponential backoff

### TDD Цикл 9.2: Ротация файлов

#### RED: Тест ротации
```python
def test_interceptor_handles_file_rotation(tmp_path):
    """LogInterceptor должен обрабатывать ротацию лог-файла"""
    source_file = tmp_path / "app.log"
    source_file.write_text("Initial\n")
    
    interceptor = LogInterceptor(source_file=source_file, use_buffer=True)
    interceptor.start()
    
    writer = MockLogWriter(source_file, append=True)
    writer.write_line("Line before rotation")
    time.sleep(0.3)
    
    # Ротация: переименовываем старый файл, создаём новый
    rotated_file = tmp_path / "app.log.1"
    source_file.rename(rotated_file)
    source_file.write_text("")  # Новый файл
    
    writer = MockLogWriter(source_file, append=True)
    writer.write_line("Line after rotation")
    time.sleep(0.5)
    
    lines = interceptor.get_buffered_lines()
    interceptor.stop()
    
    assert "Line before rotation" in lines
    assert "Line after rotation" in lines
```

#### GREEN: Обработка ротации через watchdog events

### Deliverables:
- ✅ Обработка ошибок файловой системы
- ✅ Retry механизм с exponential backoff
- ✅ Поддержка ротации файлов
- ✅ Логирование ошибок

---

## Итерация 10: Метаданные и временные метки

### TDD Цикл 10.1: Добавление timestamp к строкам

#### RED: Тесты timestamp
```python
def test_interceptor_adds_timestamps(tmp_path):
    """LogInterceptor должен добавлять timestamp к захваченным строкам"""
    source_file = tmp_path / "app.log"
    target_file = tmp_path / "captured.log"
    source_file.touch()
    
    interceptor = LogInterceptor(
        source_file=source_file,
        target_file=target_file,
        add_timestamps=True
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

def test_interceptor_get_lines_with_metadata(tmp_path):
    """LogInterceptor должен возвращать строки с метаданными"""
    source_file = tmp_path / "app.log"
    source_file.touch()
    
    interceptor = LogInterceptor(source_file=source_file, use_buffer=True)
    interceptor.start()
    
    writer = MockLogWriter(source_file)
    writer.write_line("Test")
    time.sleep(0.3)
    
    lines_with_meta = interceptor.get_lines_with_metadata()
    interceptor.stop()
    
    assert len(lines_with_meta) > 0
    entry = lines_with_meta[0]
    assert "line" in entry
    assert "timestamp" in entry
    assert "event_id" in entry
```

#### GREEN: Реализация timestamp и metadata

### Deliverables:
- ✅ ISO 8601 timestamps
- ✅ Метаданные в выходном файле
- ✅ API для получения строк с метаданными

---

## Итерация 11: Управление состоянием и статистика

### TDD Цикл 11.1: Pause/Resume

#### RED: Тесты pause/resume
```python
def test_interceptor_pause_resume(tmp_path):
    """LogInterceptor должен поддерживать pause/resume"""
    source_file = tmp_path / "app.log"
    source_file.touch()
    
    interceptor = LogInterceptor(source_file=source_file, use_buffer=True)
    interceptor.start()
    
    writer = MockLogWriter(source_file)
    writer.write_line("Line 1")
    time.sleep(0.2)
    
    interceptor.pause()
    assert interceptor.is_paused()
    
    # Строки во время паузы не должны захватываться
    writer.write_line("Line during pause")
    time.sleep(0.2)
    
    interceptor.resume()
    assert not interceptor.is_paused()
    
    writer.write_line("Line 2")
    time.sleep(0.2)
    
    lines = interceptor.get_buffered_lines()
    interceptor.stop()
    
    assert "Line 1" in lines
    assert "Line 2" in lines
    assert "Line during pause" not in lines
```

#### GREEN: Реализация pause/resume

### TDD Цикл 11.2: Статистика

#### RED: Тесты статистики
```python
def test_interceptor_statistics(tmp_path):
    """LogInterceptor должен собирать статистику"""
    source_file = tmp_path / "app.log"
    source_file.touch()
    
    interceptor = LogInterceptor(source_file=source_file)
    interceptor.start()
    
    writer = MockLogWriter(source_file)
    writer.write_line("Line 1")
    writer.write_line("Line 2")
    writer.write_line("Line 3")
    time.sleep(0.3)
    
    stats = interceptor.get_stats()
    interceptor.stop()
    
    assert stats["lines_captured"] == 3
    assert stats["events_processed"] >= 1
    assert "start_time" in stats
    assert "uptime_seconds" in stats
```

#### GREEN: Реализация сбора статистики

### Deliverables:
- ✅ Pause/Resume функциональность
- ✅ Методы is_paused(), get_stats()
- ✅ Статистика работы

---

## Итерация 12: Pytest фикстуры и интеграция

### TDD Цикл 12.1: Pytest fixtures

#### RED: Тесты с использованием fixtures
```python
# tests/conftest.py
@pytest.fixture
def log_interceptor(tmp_path):
    """Фикстура для LogInterceptor с временными файлами"""
    source_file = tmp_path / "app.log"
    source_file.touch()
    
    interceptor = LogInterceptor(source_file=source_file, use_buffer=True)
    yield interceptor
    
    if interceptor.is_running():
        interceptor.stop()

@pytest.fixture
def mock_log_writer(tmp_path):
    """Фикстура для MockLogWriter"""
    log_file = tmp_path / "app.log"
    writer = MockLogWriter(log_file)
    yield writer
    writer.cleanup()
```

#### GREEN: Создание удобных fixtures

### Deliverables:
- ✅ Pytest fixtures в conftest.py
- ✅ Интеграционные тесты с реальными сценариями

---

## Итерация 13: Документация и примеры

### Задачи:
1. Обновить README.md с примерами использования
2. Написать API.md с полной документацией API
3. Добавить docstrings ко всем публичным методам
4. Создать examples/ директорию с примерами:
   - Базовое использование
   - С фильтрами
   - С callbacks
   - Integration в pytest

### Deliverables:
- ✅ Полная документация
- ✅ Примеры использования
- ✅ Docstrings

---

## Итерация 14: Продвинутые фичи

### TDD Цикл 14.1: Debounce механизм

#### RED: Тесты debounce
```python
def test_interceptor_debounce_prevents_duplicates(tmp_path):
    """Debounce должен предотвращать обработку дублирующихся событий"""
    source_file = tmp_path / "app.log"
    source_file.touch()
    
    config = InterceptorConfig(debounce_interval=0.5)
    interceptor = LogInterceptor(
        source_file=source_file,
        config=config,
        use_buffer=True
    )
    interceptor.start()
    
    # Быстрые множественные записи
    writer = MockLogWriter(source_file)
    for i in range(10):
        writer.write_line(f"Line {i}")
        time.sleep(0.05)  # Быстрее чем debounce
    
    time.sleep(1.0)  # Ждём завершения debounce
    
    stats = interceptor.get_stats()
    interceptor.stop()
    
    # Должно быть обработано меньше событий из-за debounce
    assert stats["events_processed"] < 10
```

#### GREEN: Реализация debounce

### TDD Цикл 14.2: Множественные файлы (опционально)

#### RED: Тест множественных файлов
```python
def test_interceptor_multiple_files(tmp_path):
    """LogInterceptor должен отслеживать несколько файлов"""
    file1 = tmp_path / "app1.log"
    file2 = tmp_path / "app2.log"
    file1.touch()
    file2.touch()
    
    interceptor = LogInterceptor(
        source_files=[file1, file2],
        use_buffer=True
    )
    interceptor.start()
    
    writer1 = MockLogWriter(file1)
    writer2 = MockLogWriter(file2)
    
    writer1.write_line("From file 1")
    writer2.write_line("From file 2")
    
    time.sleep(0.3)
    
    lines = interceptor.get_buffered_lines()
    interceptor.stop()
    
    assert "From file 1" in lines
    assert "From file 2" in lines
```

#### GREEN: Реализация multi-file support

### Deliverables:
- ✅ Debounce механизм
- ✅ Поддержка множественных файлов (опционально)

---

## Итерация 15: Производительность и оптимизация

### Задачи:
1. Провести профилирование
2. Оптимизировать горячие пути
3. Добавить benchmark тесты
4. Тестирование на больших файлах

### TDD Цикл 15.1: Performance тесты

#### RED: Benchmark тесты
```python
def test_interceptor_performance_high_volume(tmp_path, benchmark):
    """LogInterceptor должен эффективно обрабатывать большие объёмы"""
    source_file = tmp_path / "app.log"
    source_file.touch()
    
    interceptor = LogInterceptor(source_file=source_file, use_buffer=True)
    
    def write_1000_lines():
        writer = MockLogWriter(source_file)
        writer.write_burst([f"Line {i}" for i in range(1000)], interval=0.001)
    
    interceptor.start()
    elapsed = benchmark(write_1000_lines)
    time.sleep(1.0)
    
    stats = interceptor.get_stats()
    interceptor.stop()
    
    assert stats["lines_captured"] == 1000
    assert elapsed < 5.0  # Должно завершиться за 5 секунд
```

#### GREEN: Оптимизация

### Deliverables:
- ✅ Оптимизированный код
- ✅ Benchmark тесты
- ✅ Производительность документирована

---

## Итерация 16: CI/CD и финальная полировка

### Задачи:
1. Настроить GitHub Actions:
   - Запуск тестов на Linux и Windows
   - Python 3.9, 3.10, 3.11, 3.12
   - Coverage отчёты
   - Линтинг (ruff, pyright)
2. Настроить pre-commit hooks
3. Создать CHANGELOG.md
4. Подготовить к релизу

### Deliverables:
- ✅ GitHub Actions workflows
- ✅ Pre-commit configuration
- ✅ CHANGELOG.md
- ✅ Готово к релизу

---

## Критерии завершения проекта

### Функциональность:
- ✅ Все базовые требования (1-9) реализованы
- ✅ Расширенные требования (10-22) реализованы
- ✅ Дополнительные требования (23-24) выполнены

### Качество кода:
- ✅ Test coverage >= 90%
- ✅ Все тесты проходят на Linux и Windows
- ✅ Нет ошибок линтера
- ✅ Полные type hints

### Документация:
- ✅ README с примерами
- ✅ API documentation
- ✅ Docstrings для всех публичных API
- ✅ CHANGELOG

### CI/CD:
- ✅ GitHub Actions настроен
- ✅ Автоматическое тестирование
- ✅ Coverage reporting

---

## Порядок работы по TDD

Для каждой итерации следовать циклу:

1. **RED** - Написать тест, который падает
   - Тест должен проверять одну конкретную функциональность
   - Запустить тест и убедиться, что он падает
   
2. **GREEN** - Написать минимальный код для прохождения теста
   - Реализовать только то, что нужно для теста
   - Не думать об оптимизации
   - Запустить тест и убедиться, что он проходит
   
3. **REFACTOR** - Улучшить код
   - Убрать дублирование
   - Улучшить читаемость
   - Оптимизировать при необходимости
   - Убедиться, что все тесты всё ещё проходят

4. **Повторить** для следующей функциональности

---

## Инструменты и команды

### Запуск тестов:
```bash
# Все тесты
pytest

# С покрытием
pytest --cov=log_interceptor --cov-report=html

# Конкретный файл
pytest tests/test_interceptor.py

# Конкретный тест
pytest tests/test_interceptor.py::test_interceptor_captures_new_lines

# С выводом print
pytest -s
```

### Линтинг:
```bash
# Ruff
ruff check .
ruff format .

# Pyright
pyright
```

### Структура коммита:
```
feat: добавить базовую функциональность LogInterceptor
test: добавить тесты для фильтров
refactor: улучшить обработку ошибок
docs: обновить README с примерами
```

---

## Приоритеты

### Must Have (Итерации 1-9):
- MockLogWriter
- Базовый мониторинг файлов
- Фильтрация
- Буферизация
- Context manager
- Обработка ошибок

### Should Have (Итерации 10-13):
- Метаданные и timestamps
- Pause/Resume
- Статистика
- Pytest fixtures
- Документация

### Nice to Have (Итерации 14-15):
- Debounce
- Множественные файлы
- Оптимизация производительности

---

## Оценка времени

| Итерация | Описание | Оценка (часы) |
|----------|----------|---------------|
| 0 | Инфраструктура | 2 |
| 1 | MockLogWriter | 4 |
| 2 | Exceptions & Config | 2 |
| 3 | Фильтры | 4 |
| 4 | Базовый мониторинг | 6 |
| 5 | Буферизация | 3 |
| 6 | Интеграция фильтров | 2 |
| 7 | Callbacks | 3 |
| 8 | Context Manager | 2 |
| 9 | Обработка ошибок | 5 |
| 10 | Метаданные | 3 |
| 11 | Управление состоянием | 4 |
| 12 | Pytest fixtures | 2 |
| 13 | Документация | 4 |
| 14 | Продвинутые фичи | 4 |
| 15 | Производительность | 3 |
| 16 | CI/CD | 3 |
| **Итого** | | **~56 часов** |

---

## Заключение

Этот план разработки следует принципам TDD и обеспечивает:
- Пошаговое создание функциональности
- Высокое покрытие тестами
- Качественный, поддерживаемый код
- Полную документацию
- Production-ready библиотеку

Каждая итерация может выполняться независимо, что позволяет гибко управлять процессом разработки.

