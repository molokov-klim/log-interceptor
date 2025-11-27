"""Main LogInterceptor module for log file monitoring and interception.

Provides LogInterceptor class for tracking log file changes
in real-time using watchdog.
"""

from __future__ import annotations

import logging
import sys
import threading
import time
from collections import deque
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Literal, TypedDict

from watchdog.events import FileSystemEventHandler

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

if TYPE_CHECKING:
    import types
    from collections.abc import Sequence

    from watchdog.events import FileSystemEvent
    from watchdog.observers import Observer

    from log_interceptor.config import InterceptorConfig
    from log_interceptor.filters import BaseFilter


class LineMetadata(TypedDict):
    """Metadata for log line."""

    line: str
    timestamp: float
    event_id: int

# Type for callback functions
CallbackType = Callable[[str, float, int], None]

# Configure logger for internal errors
logger = logging.getLogger(__name__)


class _LogFileEventHandler(FileSystemEventHandler):
    """File system event handler for log file monitoring."""

    def __init__(self, interceptor: "LogInterceptor") -> None:  # noqa: UP037
        """Initialize event handler.

        Args:
            interceptor: LogInterceptor instance that uses this handler.

        """
        super().__init__()
        self.interceptor = interceptor

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file modification event.

        Args:
            event: File modification event.

        """
        if event.is_directory:
            return

        # Check that our file was modified
        event_path = str(event.src_path) if isinstance(event.src_path, bytes) else event.src_path
        if Path(event_path).resolve() == self.interceptor.source_file.resolve():
            self.interceptor._process_new_lines()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]


class LogInterceptor:
    """Log interceptor for monitoring file changes in real-time.

    Uses watchdog to track file system changes
    and captures new lines from log file.
    """

    def __init__(  # noqa: PLR0913
        self,
        source_file: Path | str,
        *,
        target_file: Path | str | None = None,
        allow_missing: bool = False,
        use_buffer: bool = False,
        buffer_size: int = 1000,
        overflow_strategy: Literal["FIFO"] = "FIFO",
        filters: Sequence[BaseFilter] | None = None,
        config: InterceptorConfig | None = None,
        add_timestamps: bool = False,
    ) -> None:
        """Initialize LogInterceptor.

        Args:
            source_file: Path to source log file for monitoring.
            target_file: Path to target file for writing captured lines.
            allow_missing: If True, doesn't require file existence at initialization.
            use_buffer: If True, enables in-memory line buffering.
            buffer_size: Maximum buffer size in memory.
            overflow_strategy: Buffer overflow strategy ("FIFO").
            filters: List of filters to apply to new lines.
            config: Configuration object for advanced settings.
            add_timestamps: If True, adds ISO 8601 timestamp to lines in target_file.

        Raises:
            FileNotFoundError: If source_file doesn't exist and allow_missing=False.

        """
        self.source_file = Path(source_file)
        self.target_file = Path(target_file) if target_file else None

        if not allow_missing and not self.source_file.exists():
            msg = f"Source file not found: {source_file}"
            raise FileNotFoundError(msg)

        self._running = False
        self._paused = False
        self._observer: "Observer | None" = None  # noqa: UP037  # pyright: ignore[reportInvalidTypeForm]
        self._file_position = 0

        # Statistics
        self._lines_captured = 0
        self._events_processed = 0
        self._start_time: float | None = None

        # Debounce mechanism
        self._last_event_time: float | None = None

        # Save configuration or use default values
        if config:
            from log_interceptor.config import InterceptorConfig  # noqa: PLC0415

            self._config = config
        else:
            from log_interceptor.config import InterceptorConfig  # noqa: PLC0415

            self._config = InterceptorConfig()

        # Initialize in-memory buffer
        self._buffer: deque[str] | None = deque(maxlen=buffer_size) if use_buffer else None
        self._buffer_lock = threading.Lock()
        self._overflow_strategy = overflow_strategy

        # Initialize metadata buffer
        self._metadata_buffer: deque[LineMetadata] = deque(maxlen=buffer_size)
        self._metadata_lock = threading.Lock()

        # Initialize filters
        self._filters: Sequence[BaseFilter] = filters if filters else []

        # Initialize callback system
        self._callbacks: list[CallbackType] = []
        self._callbacks_lock = threading.Lock()
        self._event_counter = 0

        # Timestamp settings
        self._add_timestamps = add_timestamps

        # Initialize file position (if file exists)
        if self.source_file.exists():
            self._file_position = self.source_file.stat().st_size

    def is_running(self) -> bool:
        """Check if monitoring is running.

        Returns:
            True if monitoring is active, False otherwise.

        """
        return self._running

    def start(self) -> None:
        """Start log file monitoring.

        Raises:
            RuntimeError: If monitoring is already running.

        """
        if self._running:
            msg = "LogInterceptor is already running"
            raise RuntimeError(msg)

        self._running = True
        self._start_time = time.time()

        # Create and start watchdog observer
        from watchdog.observers import Observer as WatchdogObserver  # noqa: PLC0415

        self._observer = WatchdogObserver()  # pyright: ignore[reportUnknownMemberType]
        event_handler = _LogFileEventHandler(self)
        watch_path = str(self.source_file.parent)
        self._observer.schedule(event_handler, watch_path, recursive=False)  # pyright: ignore[reportUnknownMemberType, reportOptionalMemberAccess]
        self._observer.start()  # pyright: ignore[reportUnknownMemberType, reportOptionalMemberAccess]

    def stop(self) -> None:
        """Stop log file monitoring."""
        if not self._running:
            return

        self._running = False

        # Stop observer
        if self._observer:  # pyright: ignore[reportUnknownMemberType]
            self._observer.stop()  # pyright: ignore[reportUnknownMemberType]
            self._observer.join(timeout=1.0)  # pyright: ignore[reportUnknownMemberType]
            self._observer = None

    def get_buffered_lines(self) -> Sequence[str]:
        """Return current in-memory buffer contents.

        Returns:
            List of lines from buffer. Empty list if buffering is not enabled.

        """
        if not self._buffer:
            return []
        with self._buffer_lock:
            return list(self._buffer)

    def clear_buffer(self) -> None:
        """Clear in-memory buffer.

        Removes all lines from buffer. Does nothing if buffering is not enabled.

        """
        if not self._buffer:
            return
        with self._buffer_lock:
            self._buffer.clear()

    def get_lines_with_metadata(self) -> list[LineMetadata]:
        """Return list of lines with metadata.

        Returns:
            List of dictionaries with keys: line, timestamp, event_id.

        """
        with self._metadata_lock:
            return list(self._metadata_buffer)

    def pause(self) -> None:
        """Pause capturing new lines without stopping watchdog."""
        self._paused = True

    def resume(self) -> None:
        """Resume capturing new lines after pause."""
        self._paused = False

    def is_paused(self) -> bool:
        """Check if interceptor is paused.

        Returns:
            True if paused, False otherwise.

        """
        return self._paused

    def get_stats(self) -> dict[str, int | float]:
        """Return interceptor statistics.

        Returns:
            Dictionary with statistics: lines_captured, events_processed, start_time, uptime_seconds.

        """
        uptime = 0.0
        if self._start_time is not None:
            uptime = time.time() - self._start_time

        return {
            "lines_captured": self._lines_captured,
            "events_processed": self._events_processed,
            "start_time": self._start_time or 0.0,
            "uptime_seconds": uptime,
        }

    def add_callback(self, callback: CallbackType) -> None:
        """Add callback function for new line notifications.

        Args:
            callback: Function with signature (line: str, timestamp: float, event_id: int) -> None

        """
        with self._callbacks_lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

    def remove_callback(self, callback: CallbackType) -> None:
        """Remove callback function from list.

        Args:
            callback: Function to remove.

        """
        with self._callbacks_lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    def __enter__(self) -> Self:
        """Enter context manager.

        Automatically starts monitoring.

        Returns:
            LogInterceptor instance.

        """
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Exit context manager.

        Automatically stops monitoring and releases resources.

        Args:
            exc_type: Exception type (if any).
            exc_val: Exception value (if any).
            exc_tb: Exception traceback (if any).

        """
        self.stop()

    def _invoke_callbacks(self, line: str, timestamp: float, event_id: int) -> None:
        """Invoke all registered callbacks for log line.

        Args:
            line: Log line to pass to callbacks.
            timestamp: Event timestamp.
            event_id: Unique event identifier.

        """
        if not self._callbacks:
            return

        # Copy callbacks list under lock
        with self._callbacks_lock:
            callbacks_copy = self._callbacks.copy()

        # Invoke callbacks outside lock
        for callback in callbacks_copy:
            try:
                callback(line, timestamp, event_id)
            except Exception:  # noqa: PERF203
                # Log error but don't interrupt processing
                logger.exception("Error in callback %s", callback.__name__)

    def _apply_filters(self, line: str) -> bool:
        """Apply filters to log line.

        Args:
            line: Line to filter.

        Returns:
            True if line passed all filters, False otherwise.

        """
        if not self._filters:
            return True

        # Apply all filters (AND logic)
        return all(filter_obj.filter(line) for filter_obj in self._filters)

    def _process_new_lines(self) -> None:  # noqa: C901, PLR0912, PLR0915
        """Process new lines from log file with error handling."""
        try:
            if not self.source_file.exists():
                return

            # Debounce mechanism: check if enough time passed since last event
            current_time = time.time()
            is_debounced_event = False
            if self._last_event_time is not None:
                time_since_last = current_time - self._last_event_time
                if time_since_last < self._config.debounce_interval:
                    # Event is too close to previous, mark as debounced
                    is_debounced_event = True
                else:
                    # Enough time passed, update time
                    self._last_event_time = current_time
            else:
                # First event
                self._last_event_time = current_time

            # If paused, update position but don't process lines
            if self._paused:
                current_size = self.source_file.stat().st_size
                self._file_position = current_size
                return

            # Get current file size
            current_size = self.source_file.stat().st_size

            # If file was truncated or rotated, reset position
            if current_size < self._file_position:
                logger.info("File rotation detected for %s, resetting position", self.source_file)
                self._file_position = 0

            # Read new lines
            if current_size > self._file_position:
                with self.source_file.open("r", encoding=self._config.encoding) as f:
                    f.seek(self._file_position)
                    new_lines = f.readlines()

                # Apply filters to lines
                filtered_lines = [line for line in new_lines if self._apply_filters(line)]

                # Increment counters
                if filtered_lines:
                    self._lines_captured += len(filtered_lines)
                    # Increment events_processed only if not debounced event
                    if not is_debounced_event:
                        self._events_processed += 1

                # Process each filtered line
                for line in filtered_lines:
                    # Get metadata
                    timestamp = time.time()
                    event_id = self._event_counter
                    self._event_counter += 1

                    # Save metadata
                    metadata: LineMetadata = {
                        "line": line.rstrip("\n"),
                        "timestamp": timestamp,
                        "event_id": event_id,
                    }
                    with self._metadata_lock:
                        self._metadata_buffer.append(metadata)

                    # Write to buffer (if enabled)
                    if self._buffer is not None:
                        with self._buffer_lock:
                            self._buffer.append(line)

                    # Invoke callbacks
                    self._invoke_callbacks(line, timestamp, event_id)

                # Write filtered lines to target file
                if self.target_file and filtered_lines:
                    with self.target_file.open("a", encoding=self._config.encoding) as f:
                        for line in filtered_lines:
                            if self._add_timestamps:
                                # Format timestamp as ISO 8601
                                dt = datetime.fromtimestamp(time.time(), tz=timezone.utc)
                                timestamp_str = dt.isoformat()
                                f.write(f"[CAPTURED_AT: {timestamp_str}] {line}")
                            else:
                                f.write(line)

                # Update position
                self._file_position = current_size

        except PermissionError:
            logger.warning("Permission denied when reading %s, will retry", self.source_file)
        except OSError:
            logger.exception("OS error when reading %s", self.source_file)
        except Exception:
            logger.exception("Unexpected error processing %s", self.source_file)
