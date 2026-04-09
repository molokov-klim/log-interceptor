"""Configuration for LogInterceptor.

Provides InterceptorConfig class with default settings
and presets for various usage scenarios.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

from log_interceptor.exceptions import ConfigurationError


@dataclass(frozen=True)
class InterceptorConfig:
    """Configuration for LogInterceptor.

    Attributes:
        debounce_interval: Debounce interval for file system events (in seconds).
        buffer_size: Size of internal buffer (number of lines).
        max_file_size: Maximum file size for monitoring (in bytes), None = no limit.
        encoding: File encoding.
        follow_rotations: Follow file rotations.
        retry_on_error: Retry operations on errors.
        retry_max_attempts: Maximum number of retry attempts.
        retry_delay: Delay between retry attempts (in seconds).

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
        """Validate parameters after initialization."""
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
        """Create configuration from preset.

        Args:
            preset: Preset name ('aggressive', 'balanced', 'conservative').
            **overrides: Parameters to override preset values.

        Returns:
            InterceptorConfig instance with settings from preset.

        Raises:
            ConfigurationError: If preset is unknown.

        """
        presets: dict[str, dict[str, float | int]] = {
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

        # Merge preset and overrides
        config_dict: dict[str, Any] = {**presets[preset], **overrides}
        return cls(**config_dict)
