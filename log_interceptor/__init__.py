"""LogInterceptor - библиотека для перехвата и мониторинга лог-файлов в реальном времени.

Основные компоненты:
    - LogInterceptor: Основной класс для мониторинга лог-файлов
    - InterceptorConfig: Класс конфигурации
    - Фильтры: BaseFilter, RegexFilter, PredicateFilter, CompositeFilter
    - Исключения: LogInterceptorError, FileWatchError, FilterError, LogBufferError, ConfigurationError

Пример использования:
    >>> from log_interceptor import LogInterceptor
    >>> interceptor = LogInterceptor(source_file="app.log", target_file="captured.log")
    >>> interceptor.start()
    >>> # ... мониторинг работает ...
    >>> interceptor.stop()
"""

from __future__ import annotations

from log_interceptor.config import InterceptorConfig
from log_interceptor.exceptions import (
    ConfigurationError,
    FileWatchError,
    FilterError,
    LogBufferError,
    LogInterceptorError,
)
from log_interceptor.filters import (
    BaseFilter,
    CompositeFilter,
    PredicateFilter,
    RegexFilter,
)
from log_interceptor.interceptor import LogInterceptor

__version__ = "0.1.0"

__all__ = [
    "BaseFilter",
    "CompositeFilter",
    "ConfigurationError",
    "FileWatchError",
    "FilterError",
    "InterceptorConfig",
    "LogBufferError",
    "LogInterceptor",
    "LogInterceptorError",
    "PredicateFilter",
    "RegexFilter",
    "__version__",
]
