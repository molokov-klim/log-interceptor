# LogInterceptor — Technical Specifications

## Overview

**LogInterceptor** is a Python library for intercepting and monitoring changes in external log files in real-time. It
captures new log entries without blocking the main execution thread, making it ideal for automated testing and
application monitoring.

### Key Features

- **Cross-platform**: Works on Linux and Windows
- **Non-blocking**: Uses separate threads for log monitoring
- **Flexible**: Multiple filtering, buffering, and callback options
- **Reliable**: Thread-safe with comprehensive error handling
- **Production-ready**: Type hints, logging, and pytest integration

***

## Core Requirements

### 1. Primary Purpose

- Monitor changes in external application log files
- Automatically copy new log entries to internal file or buffer
- Support further processing of captured logs

### 2. Cross-Platform Support

- Support for Linux and Windows
- Minimal dependencies (watchdog only)
- Correct path handling and encoding on both OS

### 3. File Change Detection

- Use watchdog library for filesystem events (on_modified)
- Handle log file rotation (rename/recreate scenarios)
- Continuous tracking of new data

### 4. Non-Blocking Execution

- Does not block main program/test thread
- Uses separate thread (threading) or process (multiprocessing)
- Proper thread/process shutdown and cleanup

### 5. API & Management

- Methods: `start()`, `stop()`, or context manager support
- Retrieve new lines via buffer, file, or callbacks
- Support multiple file subscriptions (optional)

### 6. Minimal Dependencies

- Primary dependency: watchdog
- No heavy frameworks

### 7. Reliability

- Handle errors: missing files, permission changes, file locks, gaps
- Guarantee data integrity: no loss or duplication

### 8. Integration with Tests

- Easy pytest fixture integration
- Support both file output and in-memory event collection

### 9. Documentation

- README with basic to advanced examples
- Docstrings for all public methods/classes

***

## Advanced Requirements

### 10. Filesystem Event Filtering

- Ignore specific event types (e.g., only on_modified)
- Ignore non-target files
- Support filename masks (`*.log`, `app-*.log`)
- Debounce mechanism to prevent duplicate event processing

### 11. Log Content Filtering

- Filter new lines by regex or predicate function
- Write only matching lines to target file
- Support blacklist and whitelist filters
- Combine multiple filters with AND/OR logic

### 12. Thread Safety

- Thread-safe buffer operations
- Use `threading.Lock` or `threading.RLock` for critical sections
- Safe concurrent access from watchdog thread and main thread
- Safe state snapshots without race conditions

### 13. Async Callbacks

- Register custom callbacks for new log entries
- Callbacks execute asynchronously (from watchdog thread)
- Error handling in callbacks without stopping monitoring
- Callback parameters: line, timestamp, event_id

### 14. Event Buffering

- In-memory buffer option (ring buffer or queue)
- Configurable buffer size (lines or bytes)
- Overflow strategies: FIFO, LIFO, or circular
- Buffer slicing (last N lines, time-range queries)

### 15. Monitoring Status Control

- Status methods: `is_running()`, `is_paused()`, `get_stats()`
- Pause/resume without stopping watchdog
- Statistics: event count, line count, start/stop times

### 16. Error Handling

- Handle: PermissionError, IOError, FileNotFoundError
- Recovery from temporary file unavailability (retry with exponential backoff)
- Optional logging via standard logging module
- Preserve file position on failure

### 17. Context Manager & Lifecycle

- Support `with` statement (`__enter__`, `__exit__`)
- Guaranteed resource cleanup (threads, file handles)
- `__del__` as failsafe

### 18. Metadata & Timestamps

- ISO 8601 timestamps for each captured line
- Optional metadata in output file (`[CAPTURED_AT: ...]`)
- Session start/stop times
- Retrieve lines with timestamps

### 19. Logging & Diagnostics

- Built-in logging (via standard logging module)
- Debug mode support
- Error/exception tracking
- Missing/lost event reporting

### 20. Configuration & Flexibility

- Configure via: constructor parameters, config dict, environment variables
- Presets: `aggressive`, `balanced`, `conservative`

### 21. Testability

- Mockable watchdog objects
- Unit testing support with temp files
- Deterministic behavior (reproducibility)
- pytest fixtures

### 22. Performance

- Minimal CPU and memory usage
- Optimization for high-volume logs
- Configurable polling interval
- asyncio option for high-load scenarios

***

## Additional Requirements

### 23. Versioning & Python Support

- Python 3.9+
- Compatible with pytest, unittest
- Semantic versioning (semver)
- CHANGELOG with breaking changes

### 24. Project Structure

- Standard Python package (pyproject.toml, tests/, docs/)
- Full type hints
- ruff/pyright linting
- GitHub Actions CI/CD

***

# LogInterceptor — Техническое описание

## Обзор

**LogInterceptor** — это библиотека Python для отслеживания и перехвата изменений во внешних лог-файлах в реальном
времени. Захватывает новые записи без блокировки основного потока выполнения, идеальна для автотестов и мониторинга
приложений.

### Основные возможности

- **Кроссплатформенность**: работает на Linux и Windows
- **Неблокирующее выполнение**: использует отдельные потоки для мониторинга
- **Гибкость**: множество опций фильтрации, буферизации и callback'ов
- **Надёжность**: потокобезопасность и обработка ошибок
- **Production-ready**: type hints, логирование, интеграция с pytest

***

## Базовые требования

### 1. Основное назначение

- Отслеживание изменений в лог-файле внешнего приложения
- Автоматическое копирование новых записей во внутренний файл или буфер
- Поддержка дальнейшей обработки захватанных логов

### 2. Кроссплатформенность

- Поддержка Linux и Windows
- Минимальные зависимости (только watchdog)
- Корректная работа с путями и кодировками на обеих ОС

### 3. Обнаружение изменений файла

- Использование watchdog для событий файловой системы (on_modified)
- Работа с ротацией лог-файла (переименование/пересоздание)
- Непрерывное отслеживание новых данных

### 4. Неблокирующее выполнение

- Не блокирует основной поток программы/теста
- Использует отдельный поток (threading) или процесс (multiprocessing)
- Корректная остановка и завершение потоков/процессов

### 5. API и управление

- Методы: `start()`, `stop()` или поддержка контекстного менеджера
- Получение новых строк через буфер, файл или callback'ы
- Поддержка подписки на несколько файлов (опционально)

### 6. Минимальные зависимости

- Главная зависимость: watchdog
- Без тяжёлых фреймворков

### 7. Надёжность

- Обработка ошибок: отсутствие файлов, изменение прав, блокировки, пробелы
- Гарантия целостности данных: без потерь и дубликатов

### 8. Интеграция с автотестами

- Лёгкая интеграция фикстур pytest
- Поддержка записи в файл и сбора событий в памяти

### 9. Документация

- README с примерами от простого до продвинутого использования
- Docstrings для всех публичных методов и классов

***

## Расширенные требования

### 10. Фильтрация событий файловой системы

- Игнорирование определённых типов событий (например, только on_modified)
- Игнорирование событий файлов, не совпадающих с целевым
- Поддержка масок имён файлов (`*.log`, `app-*.log`)
- Механизм debounce для предотвращения дублирования обработки событий

### 11. Фильтрация содержимого логов

- Фильтрация новых строк по regexp или функции-предикату
- Запись в целевой файл только совпадающих строк
- Поддержка чёрного списка (исключение) и белого списка (включение)
- Комбинирование фильтров с логикой AND/OR

### 12. Потокобезопасность

- Потокобезопасные операции с буфером
- Использование `threading.Lock` или `threading.RLock` для критических секций
- Безопасный одновременный доступ из потока watchdog и основного потока
- Безопасные снимки состояния без гонок данных

### 13. Асинхронные callback-функции

- Регистрация пользовательских callback'ов для новых строк
- Выполнение callback'ов асинхронно (из потока watchdog)
- Обработка ошибок в callback'ах без остановки мониторинга
- Параметры callback'а: строка, временная метка, идентификатор события

### 14. Буферизация событий

- Опция буфера в памяти (кольцевой буфер или очередь)
- Настраиваемый размер буфера (по строкам или байтам)
- Стратегии переполнения: FIFO, LIFO или циклический
- Срезы буфера (последние N строк, запросы по времени)

### 15. Контроль состояния мониторинга

- Методы статуса: `is_running()`, `is_paused()`, `get_stats()`
- Приостановка без остановки (pause/resume)
- Статистика: количество событий, строк, время старта/стопа

### 16. Обработка ошибок

- Обработка: PermissionError, IOError, FileNotFoundError
- Восстановление после временной недоступности (retry с exponential backoff)
- Логирование ошибок (через стандартный logging модуль)
- Сохранение позиции файла при сбое

### 17. Контекстный менеджер и жизненный цикл

- Поддержка `with` statement (`__enter__`, `__exit__`)
- Гарантированная очистка ресурсов (потоки, дескрипторы файлов)
- `__del__` как подстраховка

### 18. Метаданные и временные метки

- ISO 8601 временные метки для каждой захватанной строки
- Опция метаметок в выходном файле (`[CAPTURED_AT: ...]`)
- Времена старта/стопа сессии
- Получение строк с их временными метками

### 19. Логирование и диагностика

- Встроенное логирование (через стандартный logging модуль)
- Поддержка debug режима
- Отслеживание ошибок и исключений
- Вывод информации о потерянных событиях

### 20. Конфигурация и гибкость

- Конфигурирование через: параметры конструктора, словарь конфигурации, переменные окружения
- Предустановки: `aggressive`, `balanced`, `conservative`

### 21. Тестируемость

- Mockable watchdog объекты
- Unit-тестирование с временными файлами
- Детерминированное поведение (воспроизводимость)
- pytest фикстуры

### 22. Производительность

- Минимальное использование CPU и памяти
- Оптимизация для больших объёмов логов
- Настраиваемый интервал опроса
- asyncio как опция для высоконагруженных сценариев

***

## Дополнительные требования

### 23. Версионирование и поддержка Python

- Python 3.9+
- Совместимость с pytest, unittest
- Semantic versioning (semver)
- CHANGELOG с breaking changes

### 24. Структура проекта

- Стандартная структура пакета Python (pyproject.toml, tests/, docs/)
- Полные type hints
- Linting с ruff/pyright
- GitHub Actions CI/CD

***
