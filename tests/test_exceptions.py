"""Тесты для пользовательских исключений LogInterceptor."""

import pytest

from log_interceptor.exceptions import (
    ConfigurationError,
    FileWatchError,
    FilterError,
    LogBufferError,
    LogInterceptorError,
)


@pytest.mark.unit
def test_interceptor_error_hierarchy() -> None:
    """Все исключения должны наследоваться от LogInterceptorError."""
    assert issubclass(FileWatchError, LogInterceptorError)
    assert issubclass(FilterError, LogInterceptorError)
    assert issubclass(LogBufferError, LogInterceptorError)
    assert issubclass(ConfigurationError, LogInterceptorError)


@pytest.mark.unit
def test_log_interceptor_error_is_exception() -> None:
    """LogInterceptorError должен наследоваться от Exception."""
    assert issubclass(LogInterceptorError, Exception)


@pytest.mark.unit
def test_file_watch_error_creation() -> None:
    """FileWatchError должен создаваться с сообщением."""
    error = FileWatchError("File not found")
    assert str(error) == "File not found"
    assert isinstance(error, LogInterceptorError)


@pytest.mark.unit
def test_filter_error_creation() -> None:
    """FilterError должен создаваться с сообщением."""
    error = FilterError("Invalid regex pattern")
    assert str(error) == "Invalid regex pattern"
    assert isinstance(error, LogInterceptorError)


@pytest.mark.unit
def test_buffer_error_creation() -> None:
    """LogBufferError должен создаваться с сообщением."""
    error = LogBufferError("Buffer overflow")
    assert str(error) == "Buffer overflow"
    assert isinstance(error, LogInterceptorError)


@pytest.mark.unit
def test_configuration_error_creation() -> None:
    """ConfigurationError должен создаваться с сообщением."""
    error = ConfigurationError("Invalid preset")
    assert str(error) == "Invalid preset"
    assert isinstance(error, LogInterceptorError)


@pytest.mark.unit
def test_exceptions_can_be_raised() -> None:
    """Исключения должны корректно выбрасываться и ловиться."""
    msg = "Test error"
    with pytest.raises(LogInterceptorError):
        raise FileWatchError(msg)

    with pytest.raises(FileWatchError):
        raise FileWatchError(msg)

    with pytest.raises(FilterError):
        raise FilterError(msg)


def _raise_chained_exception() -> None:
    """Вспомогательная функция для генерации цепочки исключений."""
    try:
        msg = "Original error"
        raise ValueError(msg)
    except ValueError as e:
        msg = "Wrapped error"
        raise FileWatchError(msg) from e


@pytest.mark.unit
def test_exceptions_with_cause() -> None:
    """Исключения должны поддерживать цепочку исключений."""
    with pytest.raises(FileWatchError) as exc_info:
        _raise_chained_exception()

    assert str(exc_info.value) == "Wrapped error"
    assert isinstance(exc_info.value.__cause__, ValueError)
    assert str(exc_info.value.__cause__) == "Original error"
