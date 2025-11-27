# Changelog

Все значительные изменения в проекте **LogInterceptor** будут документироваться в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.0.0/),
и этот проект придерживается [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

### Added
- Инфраструктура проекта
- Базовая конфигурация pyproject.toml
- GitHub Actions CI/CD pipeline
- Линтинг с ruff
- Проверка типов с pyright
- Базовый README.md

## [0.1.0] - TBD

### Планируется
- Класс `LogInterceptor` для мониторинга лог-файлов
- Система фильтров (`RegexFilter`, `PredicateFilter`, `CompositeFilter`)
- Буферизация в памяти с различными стратегиями переполнения
- Callback система для обработки новых записей
- Context manager support
- Обработка ротации файлов
- Метаданные и timestamps
- Pause/Resume функциональность
- Статистика работы
- Pytest fixtures
- Полная документация API

### Known Issues
- Проект в активной разработке

---

[Unreleased]: https://github.com/hash/log-interceptor/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/hash/log-interceptor/releases/tag/v0.1.0

