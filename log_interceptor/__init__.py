"""LogInterceptor - library for real-time log file interception and monitoring.

Main components:
    - LogInterceptor: Main class for log file monitoring
    - InterceptorConfig: Configuration class
    - Filters: BaseFilter, RegexFilter, PredicateFilter, CompositeFilter
    - Exceptions: LogInterceptorError, FileWatchError, FilterError, LogBufferError, ConfigurationError

Usage example:
    >>> from log_interceptor import LogInterceptor
    >>> interceptor = LogInterceptor(source_file="app.log", target_file="captured.log")
    >>> interceptor.start()
    >>> # ... monitoring is running ...
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
