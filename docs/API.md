# API Reference

Полная документация API для LogInterceptor.

## Содержание

- [LogInterceptor](#loginterceptor)
- [Filters](#filters)
- [Configuration](#configuration)
- [Exceptions](#exceptions)

---

## LogInterceptor

Основной класс для перехвата и мониторинга лог-файлов.

### Импорт

```python
from log_interceptor import LogInterceptor
```

### Конструктор

```python
LogInterceptor(
    source_file: Path | str,
    *,
    target_file: Path | str | None = None,
    allow_missing: bool = False,
    use_buffer: bool = False,
    buffer_size: int = 1000,
    overflow_strategy: Literal["FIFO"] = "FIFO",
    filters: Sequence[BaseFilter] | None = None,
    config: InterceptorConfig | None = None,
    add_timestamps: bool = False,
)
```

**Параметры:**

- `source_file` (Path | str): Путь к исходному лог-файлу для мониторинга
- `target_file` (Path | str | None): Путь к целевому файлу для записи захваченных строк
- `allow_missing` (bool): Если True, не требует существования файла при инициализации
- `use_buffer` (bool): Если True, включает буферизацию строк в памяти
- `buffer_size` (int): Максимальный размер буфера в памяти (строк)
- `overflow_strategy` (Literal["FIFO"]): Стратегия при переполнении буфера
- `filters` (Sequence[BaseFilter] | None): Список фильтров для применения
- `config` (InterceptorConfig | None): Объект конфигурации
- `add_timestamps` (bool): Добавлять ISO 8601 timestamp к строкам в target_file

**Raises:**

- `FileNotFoundError`: Если source_file не существует и allow_missing=False
- `ValueError`: Если overflow_strategy не "FIFO"

**Пример:**

```python
interceptor = LogInterceptor(
    source_file="app.log",
    target_file="captured.log",
    use_buffer=True,
    buffer_size=500,
    add_timestamps=True
)
```

### Методы

#### `start() -> None`

Запускает мониторинг лог-файла.

**Raises:**

- `RuntimeError`: Если мониторинг уже запущен

**Пример:**

```python
interceptor.start()
```

#### `stop() -> None`

Останавливает мониторинг лог-файла.

**Пример:**

```python
interceptor.stop()
```

#### `is_running() -> bool`

Проверяет, запущен ли мониторинг.

**Returns:** `True`, если мониторинг активен

**Пример:**

```python
if interceptor.is_running():
    print("Мониторинг активен")
```

#### `pause() -> None`

Приостанавливает захват новых строк без остановки watchdog.

**Пример:**

```python
interceptor.pause()
# Строки, записанные во время паузы, не будут захвачены
```

#### `resume() -> None`

Возобновляет захват новых строк после паузы.

**Пример:**

```python
interceptor.resume()
```

#### `is_paused() -> bool`

Проверяет, находится ли interceptor на паузе.

**Returns:** `True`, если на паузе

**Пример:**

```python
if interceptor.is_paused():
    print("На паузе")
```

#### `get_buffered_lines() -> list[str]`

Возвращает список строк из буфера памяти.

**Returns:** Список строк (пустой, если буферизация отключена)

**Пример:**

```python
lines = interceptor.get_buffered_lines()
for line in lines:
    print(line)
```

#### `clear_buffer() -> None`

Очищает буфер памяти.

**Пример:**

```python
interceptor.clear_buffer()
```

#### `get_lines_with_metadata() -> list[LineMetadata]`

Возвращает список строк с метаданными.

**Returns:** Список словарей с ключами: `line`, `timestamp`, `event_id`

**Пример:**

```python
metadata = interceptor.get_lines_with_metadata()
for entry in metadata:
    print(f"[{entry['event_id']}] {entry['timestamp']}: {entry['line']}")
```

#### `get_stats() -> dict[str, int | float]`

Возвращает статистику работы interceptor.

**Returns:** Словарь со статистикой:
- `lines_captured` (int): Общее количество захваченных строк
- `events_processed` (int): Количество обработанных событий
- `start_time` (float): Время запуска (unix timestamp)
- `uptime_seconds` (float): Время работы в секундах

**Пример:**

```python
stats = interceptor.get_stats()
print(f"Захвачено: {stats['lines_captured']} строк")
print(f"Время работы: {stats['uptime_seconds']:.2f}s")
```

#### `add_callback(callback: Callable[[str, float, int], None]) -> None`

Регистрирует callback функцию для обработки новых строк.

**Параметры:**

- `callback`: Функция, принимающая (line, timestamp, event_id)

**Пример:**

```python
def on_error(line: str, timestamp: float, event_id: int):
    if "ERROR" in line:
        print(f"Error at {timestamp}: {line}")

interceptor.add_callback(on_error)
```

#### `remove_callback(callback: Callable[[str, float, int], None]) -> None`

Удаляет зарегистрированную callback функцию.

**Параметры:**

- `callback`: Функция для удаления

**Пример:**

```python
interceptor.remove_callback(on_error)
```

### Context Manager

LogInterceptor поддерживает протокол context manager:

```python
with LogInterceptor(source_file="app.log") as interceptor:
    # Автоматический start()
    # ... ваш код ...
    pass
    # Автоматический stop()
```

---

## Filters

Система фильтрации для выборочного захвата логов.

### BaseFilter

Абстрактный базовый класс для всех фильтров.

```python
from log_interceptor.filters import BaseFilter
```

#### Метод `filter(line: str) -> bool`

Проверяет, проходит ли строка фильтр.

**Параметры:**

- `line` (str): Строка для проверки

**Returns:** `True`, если строка проходит фильтр

### RegexFilter

Фильтр на основе регулярных выражений.

```python
from log_interceptor.filters import RegexFilter
```

#### Конструктор

```python
RegexFilter(
    pattern: str,
    *,
    mode: Literal["match", "whitelist", "blacklist"] = "match",
    case_sensitive: bool = True
)
```

**Параметры:**

- `pattern` (str): Регулярное выражение
- `mode` (str): Режим фильтрации:
  - `"match"` — проверка на совпадение
  - `"whitelist"` — пропускать только совпадающие
  - `"blacklist"` — блокировать совпадающие
- `case_sensitive` (bool): Учитывать регистр

**Примеры:**

```python
# Только ERROR строки
error_filter = RegexFilter(r"ERROR", mode="whitelist")

# Исключить DEBUG строки
no_debug = RegexFilter(r"DEBUG", mode="blacklist")

# Case insensitive поиск
warn_filter = RegexFilter(r"warning", case_sensitive=False)
```

### PredicateFilter

Фильтр на основе функции-предиката.

```python
from log_interceptor.filters import PredicateFilter
```

#### Конструктор

```python
PredicateFilter(predicate: Callable[[str], bool])
```

**Параметры:**

- `predicate` (Callable): Функция, принимающая строку и возвращающая bool

**Пример:**

```python
# Только длинные строки
long_lines = PredicateFilter(lambda line: len(line) > 100)

# Только строки с timestamp
has_timestamp = PredicateFilter(lambda line: line.startswith("["))
```

### CompositeFilter

Композитный фильтр для комбинации нескольких фильтров.

```python
from log_interceptor.filters import CompositeFilter
```

#### Конструктор

```python
CompositeFilter(
    filters: Sequence[BaseFilter],
    *,
    mode: Literal["AND", "OR"] = "AND"
)
```

**Параметры:**

- `filters` (Sequence[BaseFilter]): Список фильтров
- `mode` (str): Логическая операция:
  - `"AND"` — все фильтры должны пройти
  - `"OR"` — хотя бы один фильтр должен пройти

**Пример:**

```python
from log_interceptor.filters import CompositeFilter, RegexFilter

# ERROR ИЛИ WARNING
error_or_warn = CompositeFilter([
    RegexFilter(r"ERROR"),
    RegexFilter(r"WARNING")
], mode="OR")

# ERROR И содержит "database"
error_db = CompositeFilter([
    RegexFilter(r"ERROR"),
    RegexFilter(r"database")
], mode="AND")
```

---

## Configuration

Система конфигурации для настройки поведения LogInterceptor.

### InterceptorConfig

Класс конфигурации с валидацией параметров.

```python
from log_interceptor import InterceptorConfig
```

#### Конструктор

```python
InterceptorConfig(
    debounce_interval: float = 0.1,
    buffer_size: int = 1000,
    encoding: str = "utf-8",
    read_chunk_size: int = 8192,
    retry_interval: float = 1.0,
    retry_max_attempts: int = 3,
    log_level: str = "INFO",
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
```

**Параметры:**

- `debounce_interval` (float): Интервал debounce для событий (секунды)
- `buffer_size` (int): Размер буфера в памяти
- `encoding` (str): Кодировка файлов
- `read_chunk_size` (int): Размер chunk для чтения
- `retry_interval` (float): Интервал между повторами при ошибках
- `retry_max_attempts` (int): Максимальное количество повторов
- `log_level` (str): Уровень логирования
- `log_format` (str): Формат логов

**Raises:**

- `ValueError`: Если параметры имеют недопустимые значения

**Пример:**

```python
config = InterceptorConfig(
    buffer_size=5000,
    encoding="utf-8",
    retry_max_attempts=5
)

interceptor = LogInterceptor(
    source_file="app.log",
    config=config
)
```

#### Метод `from_preset(preset: str, **overrides) -> InterceptorConfig`

Создает конфигурацию из пресета.

**Параметры:**

- `preset` (str): Имя пресета:
  - `"aggressive"` — агрессивный мониторинг (малые интервалы)
  - `"balanced"` — сбалансированный (по умолчанию)
  - `"conservative"` — консервативный (большие интервалы)
- `**overrides`: Параметры для переопределения

**Raises:**

- `ValueError`: Если preset неизвестен

**Примеры:**

```python
# Balanced preset
config = InterceptorConfig.from_preset("balanced")

# Aggressive с кастомным buffer_size
config = InterceptorConfig.from_preset("aggressive", buffer_size=10000)

# Conservative preset
config = InterceptorConfig.from_preset("conservative")
```

---

## Exceptions

Иерархия исключений для LogInterceptor.

### LogInterceptorError

Базовое исключение для всех ошибок LogInterceptor.

```python
from log_interceptor.exceptions import LogInterceptorError
```

**Пример:**

```python
try:
    interceptor.start()
except LogInterceptorError as e:
    print(f"Ошибка interceptor: {e}")
```

### FileWatchError

Исключение для ошибок мониторинга файлов.

```python
from log_interceptor.exceptions import FileWatchError
```

**Наследуется от:** `LogInterceptorError`

### FilterError

Исключение для ошибок фильтрации.

```python
from log_interceptor.exceptions import FilterError
```

**Наследуется от:** `LogInterceptorError`

**Пример:**

```python
from log_interceptor.filters import RegexFilter
from log_interceptor.exceptions import FilterError

try:
    # Невалидный regex
    filter = RegexFilter(r"[invalid(")
except FilterError as e:
    print(f"Ошибка фильтра: {e}")
```

### LogBufferError

Исключение для ошибок буферизации.

```python
from log_interceptor.exceptions import LogBufferError
```

**Наследуется от:** `LogInterceptorError`

### ConfigurationError

Исключение для ошибок конфигурации.

```python
from log_interceptor.exceptions import ConfigurationError
```

**Наследуется от:** `LogInterceptor Error`

**Пример:**

```python
from log_interceptor import InterceptorConfig
from log_interceptor.exceptions import ConfigurationError

try:
    config = InterceptorConfig(buffer_size=-1)  # Невалидное значение
except ConfigurationError as e:
    print(f"Ошибка конфигурации: {e}")
```

---

## Type Hints

### LineMetadata

TypedDict для метаданных строки.

```python
from log_interceptor.interceptor import LineMetadata

# Структура:
{
    "line": str,           # Содержимое строки
    "timestamp": float,    # Unix timestamp
    "event_id": int        # Уникальный ID события
}
```

### CallbackType

Тип для callback функций.

```python
from log_interceptor.interceptor import CallbackType

# Сигнатура:
Callable[[str, float, int], None]
# (line: str, timestamp: float, event_id: int) -> None
```

---

## Полезные примеры

### Комплексная фильтрация

```python
from log_interceptor import LogInterceptor
from log_interceptor.filters import CompositeFilter, RegexFilter, PredicateFilter

# Создаем комплексный фильтр
critical_filter = CompositeFilter([
    # Должно быть ERROR или CRITICAL
    CompositeFilter([
        RegexFilter(r"ERROR"),
        RegexFilter(r"CRITICAL")
    ], mode="OR"),
    # И должно содержать "database"
    RegexFilter(r"database"),
    # И строка должна быть достаточно длинной
    PredicateFilter(lambda line: len(line) > 50)
], mode="AND")

with LogInterceptor(
    source_file="app.log",
    filters=[critical_filter],
    use_buffer=True
) as interceptor:
    # Только критические ошибки БД с подробностями
    pass
```

### Мониторинг с обработкой

```python
from log_interceptor import LogInterceptor

def process_batch(lines):
    """Обработать пакет строк"""
    # Сохранить в БД, отправить алерт и т.д.
    pass

interceptor = LogInterceptor(source_file="app.log", use_buffer=True)
interceptor.start()

try:
    while True:
        time.sleep(5)
        
        # Приостановить для обработки
        interceptor.pause()
        
        lines = interceptor.get_buffered_lines()
        if lines:
            process_batch(lines)
            interceptor.clear_buffer()
        
        # Возобновить
        interceptor.resume()
finally:
    interceptor.stop()
```

### Аудит с метаданными

```python
from log_interceptor import LogInterceptor
import json

with LogInterceptor(source_file="app.log", use_buffer=True) as interceptor:
    # ... ваш код ...
    
    # Экспорт аудит лога с метаданными
    metadata = interceptor.get_lines_with_metadata()
    
    audit_log = {
        "session_stats": interceptor.get_stats(),
        "events": [
            {
                "id": entry["event_id"],
                "timestamp": entry["timestamp"],
                "message": entry["line"]
            }
            for entry in metadata
        ]
    }
    
    with open("audit.json", "w") as f:
        json.dump(audit_log, f, indent=2)
```

---

## См. также

- [README](../README.md) — общая информация и быстрый старт
- [Examples](../examples/) — примеры использования

