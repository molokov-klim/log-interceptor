"""Mock-объект для имитации внешнего приложения, записывающего логи.

Используется в тестах для создания контролируемых сценариев записи логов.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path
from queue import Queue
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    import types


class MockLogWriter:
    """Имитирует внешнее приложение, записывающее логи в файл."""

    def __init__(
        self,
        log_file_path: Path | str,
        *,
        thread_mode: bool = False,
        write_delay: float = 0.0,
    ) -> None:
        """Инициализирует MockLogWriter.

        Args:
            log_file_path: Путь к файлу для записи логов.
            thread_mode: Если True, работает в отдельном потоке.
            write_delay: Задержка перед каждой записью (в секундах).

        """
        self.log_file = Path(log_file_path)
        self.thread_mode = thread_mode
        self.write_delay = write_delay
        self._running = False
        self._thread: threading.Thread | None = None
        self._queue: Queue[str | None] = Queue()
        self._rotation_counter = 0

    def start(self) -> None:
        """Запускает writer в режиме потока."""
        if not self.thread_mode:
            msg = "start() доступен только в thread_mode=True"
            raise RuntimeError(msg)
        if self._running:
            msg = "Writer уже запущен"
            raise RuntimeError(msg)

        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Останавливает writer в режиме потока."""
        if not self.thread_mode:
            msg = "stop() доступен только в thread_mode=True"
            raise RuntimeError(msg)
        if not self._running:
            return

        self._running = False
        self._queue.put(None)  # Сигнал остановки
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None

    def is_running(self) -> bool:
        """Проверяет, работает ли writer.

        Returns:
            True если writer запущен, иначе False.

        """
        return self._running

    def write_line(self, line: str) -> None:
        """Записывает строку в лог-файл.

        Args:
            line: Строка для записи.

        """
        if self.thread_mode and self._running:
            self._queue.put(line)
        else:
            self._write_to_file(line)

    def _write_to_file(self, line: str) -> None:
        """Внутренний метод для записи в файл.

        Args:
            line: Строка для записи.

        """
        if self.write_delay > 0:
            time.sleep(self.write_delay)

        with self.log_file.open("a") as f:
            f.write(f"{line}\n")

    def _worker(self) -> None:
        """Рабочий поток для записи логов."""
        while self._running:
            line = self._queue.get()
            if line is None:  # Сигнал остановки
                break
            self._write_to_file(line)

    def write_burst(self, lines: list[str], interval: float = 0.0) -> None:
        """Записывает несколько строк с заданным интервалом.

        Args:
            lines: Список строк для записи.
            interval: Интервал между записями (в секундах).

        """
        for line in lines:
            self.write_line(line)
            if interval > 0:
                time.sleep(interval)

    def rotate_file(self) -> Path:
        """Имитирует ротацию лог-файла.

        Переименовывает текущий файл с добавлением суффикса и создаёт новый пустой файл.

        Returns:
            Путь к ротированному файлу.

        """
        if self.log_file.exists():
            self._rotation_counter += 1
            rotated_path = self.log_file.with_suffix(f".{self._rotation_counter}")
            self.log_file.rename(rotated_path)
            return rotated_path

        # Если файл не существует, создаём пустой ротированный файл
        self._rotation_counter += 1
        rotated_path = self.log_file.with_suffix(f".{self._rotation_counter}")
        rotated_path.touch()
        return rotated_path

    def __enter__(self) -> Self:
        """Вход в context manager.

        Returns:
            Экземпляр MockLogWriter.

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
        """Выход из context manager.

        Args:
            exc_type: Тип исключения.
            exc_val: Значение исключения.
            exc_tb: Traceback исключения.

        """
        if self.thread_mode and self._running:
            self.stop()

    def __repr__(self) -> str:
        """Строковое представление объекта.

        Returns:
            Строковое представление MockLogWriter.

        """
        status = "running" if self._running else "stopped"
        mode = "thread" if self.thread_mode else "sync"
        return f"MockLogWriter(file={self.log_file.name}, mode={mode}, status={status})"

    def get_line_count(self) -> int:
        """Возвращает количество строк в файле.

        Returns:
            Количество строк в лог-файле.

        """
        if not self.log_file.exists():
            return 0
        return len(self.log_file.read_text().splitlines())
