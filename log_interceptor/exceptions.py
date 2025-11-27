"""Custom exceptions for LogInterceptor.

Exception hierarchy:
    LogInterceptorError (base)
    ├── FileWatchError (file monitoring errors)
    ├── FilterError (filtering errors)
    ├── BufferError (buffering errors)
    └── ConfigurationError (configuration errors)
"""

from __future__ import annotations


class LogInterceptorError(Exception):
    """Base exception for all LogInterceptor errors.

    All library-specific exceptions inherit from this class,
    making it easy to catch any LogInterceptor errors.
    """


class FileWatchError(LogInterceptorError):
    """Exception for file monitoring errors.

    Raised when issues occur with:
    - Missing files
    - Insufficient access permissions
    - File system errors
    - Watchdog problems
    """


class FilterError(LogInterceptorError):
    """Exception for log filtering errors.

    Raised when issues occur with:
    - Invalid regular expressions
    - Errors in predicate functions
    - Incorrect filter configuration
    """


class LogBufferError(LogInterceptorError):
    """Exception for buffering errors.

    Raised when issues occur with:
    - Buffer overflow
    - Invalid buffer size
    - Buffer read/write errors
    """


class ConfigurationError(LogInterceptorError):
    """Exception for configuration errors.

    Raised when issues occur with:
    - Invalid configuration parameters
    - Unknown presets
    - Conflicting settings
    """
