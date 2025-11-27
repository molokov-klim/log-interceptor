"""Mock object for simulating external application writing logs.

Used in tests to create controlled log writing scenarios.
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path
from queue import Queue
from typing import TYPE_CHECKING

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

if TYPE_CHECKING:
    import types


class MockLogWriter:
    """Simulates external application writing logs to file."""

    def __init__(
        self,
        log_file_path: Path | str,
        *,
        thread_mode: bool = False,
        write_delay: float = 0.0,
    ) -> None:
        """Initialize MockLogWriter.

        Args:
            log_file_path: Path to log file for writing.
            thread_mode: If True, runs in separate thread.
            write_delay: Delay before each write (in seconds).

        """
        self.log_file = Path(log_file_path)
        self.thread_mode = thread_mode
        self.write_delay = write_delay
        self._running = False
        self._thread: threading.Thread | None = None
        self._queue: Queue[str | None] = Queue()
        self._rotation_counter = 0

    def start(self) -> None:
        """Start writer in thread mode."""
        if not self.thread_mode:
            msg = "start() only available in thread_mode=True"
            raise RuntimeError(msg)
        if self._running:
            msg = "Writer is already running"
            raise RuntimeError(msg)

        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop writer in thread mode."""
        if not self.thread_mode:
            msg = "stop() only available in thread_mode=True"
            raise RuntimeError(msg)
        if not self._running:
            return

        self._running = False
        self._queue.put(None)  # Stop signal
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    def is_running(self) -> bool:
        """Check if writer is running.

        Returns:
            True if writer is running, False otherwise.

        """
        return self._running

    def write_line(self, line: str) -> None:
        """Write line to log file.

        Args:
            line: Line to write.

        """
        if self.thread_mode and self._running:
            self._queue.put(line)
        else:
            self._write_to_file(line)

    def _write_to_file(self, line: str) -> None:
        """Write line to file internally.

        Args:
            line: Line to write.

        """
        if self.write_delay > 0:
            time.sleep(self.write_delay)

        with self.log_file.open("a") as f:
            f.write(f"{line}\n")

    def _worker(self) -> None:
        """Worker thread for writing logs."""
        while self._running:
            line = self._queue.get()
            if line is None:  # Stop signal
                break
            self._write_to_file(line)

    def write_burst(self, lines: list[str], interval: float = 0.0) -> None:
        """Write multiple lines with given interval.

        Args:
            lines: List of lines to write.
            interval: Interval between writes (in seconds).

        """
        for line in lines:
            self.write_line(line)
            if interval > 0:
                time.sleep(interval)

    def rotate_file(self) -> Path:
        """Simulate log file rotation.

        Renames current file with suffix and creates new empty file.

        Returns:
            Path to rotated file.

        """
        if self.log_file.exists():
            self._rotation_counter += 1
            rotated_path = self.log_file.with_suffix(f".{self._rotation_counter}")
            self.log_file.rename(rotated_path)
            return rotated_path

        # If file does not exist, create empty rotated file
        self._rotation_counter += 1
        rotated_path = self.log_file.with_suffix(f".{self._rotation_counter}")
        rotated_path.touch()
        return rotated_path

    def __enter__(self) -> Self:
        """Enter context manager.

        Returns:
            MockLogWriter instance.

        """
        if self.thread_mode:
            self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Exit context manager.

        Args:
            exc_type: Exception type.
            exc_val: Exception value.
            exc_tb: Exception traceback.

        """
        if self.thread_mode and self._running:
            self.stop()

    def __repr__(self) -> str:
        """Return string representation.

        Returns:
            String representation of MockLogWriter.

        """
        status = "running" if self._running else "stopped"
        mode = "thread" if self.thread_mode else "sync"
        return f"MockLogWriter(file={self.log_file.name}, mode={mode}, status={status})"

    def get_line_count(self) -> int:
        """Return number of lines in file.

        Returns:
            Number of lines in log file.

        """
        if not self.log_file.exists():
            return 0
        return len(self.log_file.read_text().splitlines())
