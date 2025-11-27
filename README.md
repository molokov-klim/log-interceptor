# LogInterceptor

[![Tests](https://github.com/hash/log-interceptor/workflows/Tests/badge.svg)](https://github.com/hash/log-interceptor/actions)
[![Ruff](https://github.com/hash/log-interceptor/workflows/Ruff/badge.svg)](https://github.com/hash/log-interceptor/actions)
[![Pyright](https://github.com/hash/log-interceptor/workflows/Pyright/badge.svg)](https://github.com/hash/log-interceptor/actions)
[![codecov](https://codecov.io/gh/hash/log-interceptor/branch/main/graph/badge.svg)](https://codecov.io/gh/hash/log-interceptor)
[![Python Version](https://img.shields.io/pypi/pyversions/log-interceptor.svg)](https://pypi.org/project/log-interceptor/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**LogInterceptor** — это Python библиотека для перехвата и мониторинга изменений во внешних лог-файлах в реальном времени. Идеальна для автотестов и мониторинга приложений.

## ✨ Основные возможности

- 🚀 **Неблокирующее выполнение** — использует отдельные потоки для мониторинга
- 🔍 **Гибкая фильтрация** — поддержка regex, функций-предикатов и композитных фильтров
- 💾 **Буферизация в памяти** — сохранение логов с различными стратегиями переполнения
- 🎯 **Callback система** — асинхронные обработчики для новых записей
- 🛡️ **Надёжность** — обработка ошибок, ротация файлов, восстановление
- 🌍 **Кроссплатформенность** — работает на Linux и Windows
- 🐍 **Python 3.9+** — полная поддержка type hints
- 🧪 **Pytest интеграция** — готовые fixtures для тестов

## 📦 Установка

```bash
pip install log-interceptor
```

Для разработки:

```bash
git clone https://github.com/hash/log-interceptor.git
cd log-interceptor
pip install -e ".[dev]"
```

## 🚀 Быстрый старт

### Базовое использование

```python
from log_interceptor import LogInterceptor

# Запись новых строк в файл
with LogInterceptor(
    source_file="app.log",
    target_file="captured.log"
) as interceptor:
    # Ваш код, который генерирует логи
    # Новые записи автоматически копируются в captured.log
    pass
```

### Буферизация в памяти

```python
from log_interceptor import LogInterceptor

interceptor = LogInterceptor(
    source_file="app.log",
    use_buffer=True,
    buffer_size=1000
)

interceptor.start()

# Ваш код
# ...

# Получить захваченные строки
lines = interceptor.get_buffered_lines()
print(lines)

interceptor.stop()
```

### Фильтрация логов

```python
from log_interceptor import LogInterceptor
from log_interceptor.filters import RegexFilter

# Захватывать только ERROR и CRITICAL
error_filter = RegexFilter(r"(ERROR|CRITICAL)", mode="whitelist")

with LogInterceptor(
    source_file="app.log",
    filters=[error_filter],
    use_buffer=True
) as interceptor:
    # Только строки с ERROR или CRITICAL попадут в буфер
    pass
```

### Использование Callbacks

```python
from log_interceptor import LogInterceptor

def on_error_logged(line, timestamp, event_id):
    if "ERROR" in line:
        print(f"Обнаружена ошибка: {line}")

interceptor = LogInterceptor(source_file="app.log")
interceptor.add_callback(on_error_logged)
interceptor.start()

# Ваш код

interceptor.stop()
```

### Интеграция с pytest

```python
import pytest
from log_interceptor import LogInterceptor

@pytest.fixture
def log_interceptor(tmp_path):
    """Фикстура для перехвата логов в тестах"""
    log_file = tmp_path / "app.log"
    log_file.touch()
    
    interceptor = LogInterceptor(
        source_file=log_file,
        use_buffer=True
    )
    interceptor.start()
    
    yield interceptor
    
    interceptor.stop()

def test_application_logs_error(log_interceptor):
    """Проверка, что приложение логирует ошибки"""
    # Ваш код, который должен создать ERROR лог
    run_application_that_logs_error()
    
    # Проверка логов
    lines = log_interceptor.get_buffered_lines()
    assert any("ERROR" in line for line in lines)
```

## 📚 Документация

Полная документация доступна в директории [docs/](docs/):

- [API Reference](docs/API.md) — описание всех классов и методов
- [Technical Specifications](Technical%20specifications.md) — детальные технические требования
- [Development Plan](dev_plan.md) — план разработки по методологии TDD

## 🔧 Разработка

### Установка окружения

```bash
# Клонировать репозиторий
git clone https://github.com/hash/log-interceptor.git
cd log-interceptor

# Установить зависимости для разработки
pip install -e ".[dev]"
```

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=log_interceptor --cov-report=html

# Только быстрые тесты
pytest -m "not slow"
```

### Линтинг и проверка типов

```bash
# Проверка кода
ruff check .

# Форматирование
ruff format .

# Проверка типов
pyright
```

## 🏗️ Архитектура

```
log-interceptor/
├── log_interceptor/          # Основной пакет
│   ├── __init__.py          # Публичный API
│   ├── interceptor.py       # Класс LogInterceptor
│   ├── filters.py           # Система фильтров
│   ├── config.py            # Конфигурация
│   └── exceptions.py        # Исключения
├── tests/                    # Тесты
│   ├── conftest.py          # Fixtures
│   ├── mock_app.py          # MockLogWriter для тестов
│   ├── test_interceptor.py  # Тесты LogInterceptor
│   └── test_filters.py      # Тесты фильтров
└── docs/                     # Документация
```

## 🤝 Вклад в проект

Мы приветствуем ваш вклад! Пожалуйста:

1. Fork репозитория
2. Создайте ветку для фичи (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'feat: add amazing feature'`)
4. Push в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

### Правила коммитов

Используем [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — новая функциональность
- `fix:` — исправление бага
- `docs:` — изменения в документации
- `test:` — добавление или изменение тестов
- `refactor:` — рефакторинг кода
- `chore:` — изменения в конфигурации, CI/CD

## 📋 Требования

- Python 3.9+
- watchdog >= 3.0.0

## 📄 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 🙏 Благодарности

- [watchdog](https://github.com/gorakhargosh/watchdog) — за отличную библиотеку мониторинга файловой системы
- Всем контрибьюторам проекта

## 📞 Контакты

- GitHub Issues: [https://github.com/hash/log-interceptor/issues](https://github.com/hash/log-interceptor/issues)
- Документация: [https://github.com/hash/log-interceptor](https://github.com/hash/log-interceptor)

## 🗺️ Roadmap

- [x] Базовый мониторинг файлов
- [x] Система фильтров
- [x] Буферизация в памяти
- [x] Callback система
- [ ] Поддержка asyncio
- [ ] Мониторинг множественных файлов
- [ ] Поддержка structured logging (JSON)
- [ ] Web UI для мониторинга

---

Made with ❤️ by Hash
