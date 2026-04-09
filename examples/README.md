# Examples

Коллекция примеров использования LogInterceptor.

## Запуск примеров

Все примеры могут быть запущены напрямую:

```bash
python examples/01_basic_usage.py
python examples/02_with_filters.py
python examples/03_with_callbacks.py
python examples/05_advanced_features.py
```

Для pytest примера:

```bash
pytest examples/04_pytest_integration.py -v
```

## Описание примеров

### 01_basic_usage.py

Базовое использование LogInterceptor:
- Context manager
- Явное управление с `start()`/`stop()`
- Запись в `target_file`

**Ключевые концепции:**
- `LogInterceptor` initialization
- Context manager protocol
- Basic file monitoring

### 02_with_filters.py

Система фильтрации:
- `RegexFilter` для паттернов
- Whitelist и blacklist режимы
- `CompositeFilter` для комбинаций
- Комплексная логика фильтрации

**Ключевые концепции:**
- `RegexFilter` modes
- `PredicateFilter` with lambdas
- `CompositeFilter` AND/OR logic
- Filter composition

### 03_with_callbacks.py

Callback система:
- Регистрация callback функций
- Реальное время обработки
- Timestamp и event_id
- Множественные callbacks

**Ключевые концепции:**
- `add_callback()` / `remove_callback()`
- Callback signature: `(line, timestamp, event_id)`
- Real-time event processing
- Multiple callback handlers

### 04_pytest_integration.py

Интеграция с pytest:
- Создание fixtures
- Тестирование логов
- Temporary paths
- Интеграционное тестирование

**Ключевые концепции:**
- pytest fixtures
- `tmp_path` usage
- Log assertions
- Integration testing patterns

### 05_advanced_features.py

Продвинутые возможности:
- Pause/Resume для контроля
- Статистика работы
- Метаданные событий
- Timestamp в файлах
- Конфигурация и пресеты

**Ключевые концепции:**
- `pause()` / `resume()` workflow
- `get_stats()` metrics
- `get_lines_with_metadata()` audit trail
- `add_timestamps` parameter
- `InterceptorConfig` and presets

## Дополнительные ресурсы

- [API Reference](../docs/API.md) — полная документация API
- [README](../README.md) — quick start guide
- [Technical Specifications](../Technical_specifications.md) — детальные требования

## Troubleshooting

### Логи не захватываются

1. Убедитесь что `source_file` существует (или используйте `allow_missing=True`)
2. Проверьте что вызван `start()`
3. Дайте время на обработку (`time.sleep()` после записи)

### Пропущены некоторые логи

1. Увеличьте `time.sleep()` после записи (watchdog может иметь задержку)
2. Проверьте фильтры — они могут блокировать строки
3. Проверьте `buffer_size` если используете буферизацию

### Callbacks не вызываются

1. Убедитесь что callback зарегистрирован до `start()`
2. Проверьте сигнатуру: `(line: str, timestamp: float, event_id: int) -> None`
3. Проверьте что нет исключений внутри callback

## Вклад в примеры

Если у вас есть интересный use case, пожалуйста:

1. Создайте новый файл `0X_your_example.py`
2. Добавьте docstring с описанием
3. Добавьте раздел в этот README
4. Отправьте Pull Request

---

Made with ❤️ for LogInterceptor users

