"""LogInterceptor - библиотека для перехвата и мониторинга лог-файлов в реальном времени.

Основные компоненты:
    - InterceptorConfig: Класс конфигурации
    - Исключения: LogInterceptorError, FileWatchError, FilterError, LogBufferError, ConfigurationError

Пример использования:
    >>> from log_interceptor import InterceptorConfig
    >>> config = InterceptorConfig.from_preset("balanced")
    >>> print(config.debounce_interval)
    0.1
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

__version__ = "0.1.0"

__all__ = [
    "ConfigurationError",
    "FileWatchError",
    "FilterError",
    "InterceptorConfig",
    "LogBufferError",
    "LogInterceptorError",
    "__version__",
]

