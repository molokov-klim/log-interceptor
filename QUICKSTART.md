# Быстрый старт для разработчика

## 🚀 Первоначальная настройка

### 1. Создайте виртуальное окружение

```bash
# Создать виртуальное окружение
python3 -m venv .venv

# Активировать (Linux/macOS)
source .venv/bin/activate

# Активировать (Windows)
.venv\Scripts\activate
```

### 2. Установите зависимости

```bash
# Установить проект в режиме разработки
make install

# или напрямую через pip
pip install -e ".[dev]"
```

### 3. Проверьте установку

```bash
# Запустить все проверки (как в CI)
make ci

# Должны пройти:
# ✅ ruff check
# ✅ ruff format
# ✅ pyright
# ✅ pytest (пока нет тестов - это нормально)
```

## 🧪 Рабочий процесс разработки

### Команды Makefile

```bash
make help           # Показать все доступные команды
make install        # Установить зависимости
make test           # Запустить тесты
make test-cov       # Тесты с покрытием
make test-quick     # Только быстрые тесты
make lint           # Проверить код линтером
make format         # Отформатировать код
make typecheck      # Проверить типы
make clean          # Очистить временные файлы
make build          # Собрать пакет
make pre-commit     # Установить pre-commit hooks
make ci             # Все проверки (как в CI)
```

### Цикл разработки по TDD

```bash
# 1. RED - Написать падающий тест
vim tests/test_feature.py
pytest tests/test_feature.py -v   # Должен упасть ❌

# 2. GREEN - Реализовать минимальный код
vim log_interceptor/feature.py
pytest tests/test_feature.py -v   # Должен пройти ✅

# 3. REFACTOR - Улучшить код
vim log_interceptor/feature.py
pytest tests/test_feature.py -v   # Всё ещё проходит ✅

# 4. Проверить линтинг и форматирование
make lint
make format

# 5. Проверить типы
make typecheck

# 6. Запустить все тесты
make test-cov
```

## 📝 Создание коммитов

### Conventional Commits

```bash
# Примеры правильных коммитов
git commit -m "feat: add MockLogWriter class"
git commit -m "test: add tests for buffer overflow"
git commit -m "fix: handle file rotation correctly"
git commit -m "docs: update README with examples"
git commit -m "refactor: simplify filter logic"
```

### Pre-commit hooks

```bash
# Установить (однократно)
make pre-commit

# После этого перед каждым коммитом будут автоматически запускаться:
# - trailing-whitespace check
# - end-of-file fixer
# - yaml/toml validation
# - ruff check + format
# - mypy (для non-test файлов)
```

## 🐛 Отладка

### Запуск конкретного теста

```bash
# Один тест
pytest tests/test_interceptor.py::test_specific_function -v

# С выводом print
pytest tests/test_interceptor.py::test_specific_function -v -s

# С отладчиком
pytest tests/test_interceptor.py::test_specific_function -v --pdb
```

### Покрытие кода

```bash
# Запустить с покрытием
make test-cov

# Открыть HTML отчёт
# Linux:
xdg-open htmlcov/index.html

# macOS:
open htmlcov/index.html

# Windows:
start htmlcov/index.html
```

## 📚 Полезные ссылки

- **План разработки:** [dev_plan.md](dev_plan.md)
- **Техническая спецификация:** [Technical specifications.md](Technical%20specifications.md)
- **API документация:** [docs/API.md](docs/API.md)
- **Руководство контрибьютора:** [CONTRIBUTING.md](CONTRIBUTING.md)

## ✅ Checklist перед PR

```bash
# 1. Все тесты проходят
make test

# 2. Покрытие >= 90%
make test-cov

# 3. Код проходит линтинг
make lint

# 4. Код отформатирован
make format

# 5. Типы проверены
make typecheck

# 6. Всё вместе (как в CI)
make ci
```

## 🎯 Следующий шаг

После настройки окружения начните с **Итерации 1: MockLogWriter** согласно [плану разработки](dev_plan.md).

---

**Вопросы?** Создайте issue или смотрите [CONTRIBUTING.md](CONTRIBUTING.md)

