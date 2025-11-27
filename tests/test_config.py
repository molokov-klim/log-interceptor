"""Тесты для класса конфигурации InterceptorConfig."""

import pytest

from log_interceptor.config import InterceptorConfig
from log_interceptor.exceptions import ConfigurationError


@pytest.mark.unit
def test_config_default_values() -> None:
    """Config должен иметь разумные значения по умолчанию."""
    config = InterceptorConfig()

    assert config.debounce_interval == 0.1
    assert config.buffer_size == 1000
    assert config.max_file_size is None
    assert config.encoding == "utf-8"
    assert config.follow_rotations is True
    assert config.retry_on_error is True
    assert config.retry_max_attempts == 3
    assert config.retry_delay == 1.0


@pytest.mark.unit
def test_config_custom_values() -> None:
    """Config должен принимать пользовательские значения."""
    config = InterceptorConfig(
        debounce_interval=0.5,
        buffer_size=5000,
        max_file_size=1024 * 1024,  # 1MB
        encoding="utf-16",
        follow_rotations=False,
        retry_on_error=False,
    )

    assert config.debounce_interval == 0.5
    assert config.buffer_size == 5000
    assert config.max_file_size == 1024 * 1024
    assert config.encoding == "utf-16"
    assert config.follow_rotations is False
    assert config.retry_on_error is False


@pytest.mark.unit
def test_config_preset_aggressive() -> None:
    """Config должен поддерживать preset 'aggressive'."""
    config = InterceptorConfig.from_preset("aggressive")

    assert config.debounce_interval == 0.01
    assert config.buffer_size == 10000
    assert config.retry_max_attempts == 5
    assert config.retry_delay == 0.5


@pytest.mark.unit
def test_config_preset_balanced() -> None:
    """Config должен поддерживать preset 'balanced'."""
    config = InterceptorConfig.from_preset("balanced")

    assert config.debounce_interval == 0.1
    assert config.buffer_size == 1000
    assert config.retry_max_attempts == 3
    assert config.retry_delay == 1.0


@pytest.mark.unit
def test_config_preset_conservative() -> None:
    """Config должен поддерживать preset 'conservative'."""
    config = InterceptorConfig.from_preset("conservative")

    assert config.debounce_interval == 0.5
    assert config.buffer_size == 500
    assert config.retry_max_attempts == 1
    assert config.retry_delay == 2.0


@pytest.mark.unit
def test_config_preset_unknown() -> None:
    """Config должен выбрасывать ошибку для неизвестного preset."""
    with pytest.raises(ConfigurationError, match="Unknown preset"):
        InterceptorConfig.from_preset("unknown")


@pytest.mark.unit
def test_config_validation_negative_debounce() -> None:
    """Config должен валидировать debounce_interval."""
    with pytest.raises(ValueError, match=r"debounce_interval.*non-negative"):
        InterceptorConfig(debounce_interval=-0.1)


@pytest.mark.unit
def test_config_validation_negative_buffer_size() -> None:
    """Config должен валидировать buffer_size."""
    with pytest.raises(ValueError, match=r"buffer_size.*positive"):
        InterceptorConfig(buffer_size=0)


@pytest.mark.unit
def test_config_validation_negative_retry_attempts() -> None:
    """Config должен валидировать retry_max_attempts."""
    with pytest.raises(ValueError, match=r"retry_max_attempts.*positive"):
        InterceptorConfig(retry_max_attempts=-1)


@pytest.mark.unit
def test_config_immutable_after_creation() -> None:
    """Config должен быть неизменяемым после создания (frozen)."""
    config = InterceptorConfig()

    with pytest.raises(AttributeError):
        config.debounce_interval = 0.5  # type: ignore[misc]


@pytest.mark.unit
def test_config_repr() -> None:
    """Config должен иметь информативный repr."""
    config = InterceptorConfig()
    repr_str = repr(config)

    assert "InterceptorConfig" in repr_str
    assert "debounce_interval" in repr_str


@pytest.mark.unit
def test_config_preset_with_overrides() -> None:
    """from_preset должен поддерживать переопределение параметров."""
    config = InterceptorConfig.from_preset("aggressive", buffer_size=2000)

    assert config.debounce_interval == 0.01  # Из preset
    assert config.buffer_size == 2000  # Переопределено
    assert config.retry_max_attempts == 5  # Из preset
