"""Конфигурация для LogInterceptor.

Предоставляет класс InterceptorConfig с настройками по умолчанию
и предустановками (presets) для различных сценариев использования.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

from log_interceptor.exceptions import ConfigurationError


@dataclass(frozen=True)
class InterceptorConfig:
    """Конфигурация для LogInterceptor.

    Attributes:
        debounce_interval: Интервал debounce для событий файловой системы (в секундах).
        buffer_size: Размер внутреннего буфера (количество строк).
        max_file_size: Максимальный размер файла для мониторинга (в байтах), None = без ограничений.
        encoding: Кодировка файла.
        follow_rotations: Следовать за ротацией файлов.
        retry_on_error: Повторять операции при ошибках.
        retry_max_attempts: Максимальное количество попыток повтора.
        retry_delay: Задержка между попытками повтора (в секундах).

    """

    debounce_interval: float = 0.1
    buffer_size: int = 1000
    max_file_size: int | None = None
    encoding: str = "utf-8"
    follow_rotations: bool = True
    retry_on_error: bool = True
    retry_max_attempts: int = 3
    retry_delay: float = 1.0

    def __post_init__(self) -> None:
        """Валидация параметров после инициализации."""
        if self.debounce_interval < 0:
            msg = "debounce_interval must be non-negative"
            raise ValueError(msg)

        if self.buffer_size <= 0:
            msg = "buffer_size must be positive"
            raise ValueError(msg)

        if self.retry_max_attempts < 0:
            msg = "retry_max_attempts must be positive"
            raise ValueError(msg)

        if self.retry_delay < 0:
            msg = "retry_delay must be non-negative"
            raise ValueError(msg)

    @classmethod
    def from_preset(cls, preset: str, **overrides: Any) -> InterceptorConfig:
        """Создаёт конфигурацию из предустановки.

        Args:
            preset: Название предустановки ('aggressive', 'balanced', 'conservative').
            **overrides: Параметры для переопределения значений из preset.

        Returns:
            Экземпляр InterceptorConfig с настройками из preset.

        Raises:
            ConfigurationError: Если preset неизвестен.

        """
        presets = {
            "aggressive": {
                "debounce_interval": 0.01,
                "buffer_size": 10000,
                "retry_max_attempts": 5,
                "retry_delay": 0.5,
            },
            "balanced": {
                "debounce_interval": 0.1,
                "buffer_size": 1000,
                "retry_max_attempts": 3,
                "retry_delay": 1.0,
            },
            "conservative": {
                "debounce_interval": 0.5,
                "buffer_size": 500,
                "retry_max_attempts": 1,
                "retry_delay": 2.0,
            },
        }

        if preset not in presets:
            msg = f"Unknown preset: {preset}. Available: {', '.join(presets.keys())}"
            raise ConfigurationError(msg)

        # Объединяем preset и переопределения
        config_dict = {**presets[preset], **overrides}
        return cls(**config_dict)

