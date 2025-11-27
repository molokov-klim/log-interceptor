"""Основной модуль LogInterceptor для мониторинга и перехвата лог-файлов.

Предоставляет класс LogInterceptor для отслеживания изменений в лог-файлах
в реальном времени с использованием watchdog.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from watchdog.events import FileSystemEventHandler

if TYPE_CHECKING:
    from watchdog.events import FileSystemEvent
    from watchdog.observers import Observer


class _LogFileEventHandler(FileSystemEventHandler):
    """Обработчик событий файловой системы для мониторинга лог-файла."""

    def __init__(self, interceptor: "LogInterceptor") -> None:  # noqa: UP037
        """Инициализирует обработчик событий.

        Args:
            interceptor: Экземпляр LogInterceptor, который использует этот обработчик.

        """
        super().__init__()
        self.interceptor = interceptor

    def on_modified(self, event: FileSystemEvent) -> None:
        """Вызывается при изменении файла.

        Args:
            event: Событие изменения файла.

        """
        if event.is_directory:
            return

        # Проверяем, что изменился именно наш файл
        event_path = str(event.src_path) if isinstance(event.src_path, bytes) else event.src_path
        if Path(event_path).resolve() == self.interceptor.source_file.resolve():
            self.interceptor._process_new_lines()  # noqa: SLF001  # pyright: ignore[reportPrivateUsage]


class LogInterceptor:
    """Перехватчик логов для мониторинга изменений в файлах в реальном времени.

    Использует watchdog для отслеживания изменений файловой системы
    и захватывает новые строки из лог-файла.
    """

    def __init__(
        self,
        source_file: Path | str,
        *,
        target_file: Path | str | None = None,
        allow_missing: bool = False,
    ) -> None:
        """Инициализирует LogInterceptor.

        Args:
            source_file: Путь к исходному лог-файлу для мониторинга.
            target_file: Путь к целевому файлу для записи захваченных строк.
            allow_missing: Если True, не требует существования файла при инициализации.

        Raises:
            FileNotFoundError: Если source_file не существует и allow_missing=False.

        """
        self.source_file = Path(source_file)
        self.target_file = Path(target_file) if target_file else None

        if not allow_missing and not self.source_file.exists():
            msg = f"Source file not found: {source_file}"
            raise FileNotFoundError(msg)

        self._running = False
        self._observer: "Observer | None" = None  # noqa: UP037  # pyright: ignore[reportInvalidTypeForm]
        self._file_position = 0

        # Инициализируем позицию в файле (если файл существует)
        if self.source_file.exists():
            self._file_position = self.source_file.stat().st_size

    def is_running(self) -> bool:
        """Проверяет, запущен ли мониторинг.

        Returns:
            True, если мониторинг активен, иначе False.

        """
        return self._running

    def start(self) -> None:
        """Запускает мониторинг лог-файла.

        Raises:
            RuntimeError: Если мониторинг уже запущен.

        """
        if self._running:
            msg = "LogInterceptor уже запущен"
            raise RuntimeError(msg)

        self._running = True

        # Создаём и запускаем watchdog observer
        from watchdog.observers import Observer as WatchdogObserver  # noqa: PLC0415

        self._observer = WatchdogObserver()  # pyright: ignore[reportUnknownMemberType]
        event_handler = _LogFileEventHandler(self)
        watch_path = str(self.source_file.parent)
        self._observer.schedule(event_handler, watch_path, recursive=False)  # pyright: ignore[reportUnknownMemberType, reportOptionalMemberAccess]
        self._observer.start()  # pyright: ignore[reportUnknownMemberType, reportOptionalMemberAccess]

    def stop(self) -> None:
        """Останавливает мониторинг лог-файла."""
        if not self._running:
            return

        self._running = False

        # Останавливаем observer
        if self._observer:  # pyright: ignore[reportUnknownMemberType]
            self._observer.stop()  # pyright: ignore[reportUnknownMemberType]
            self._observer.join(timeout=1.0)  # pyright: ignore[reportUnknownMemberType]
            self._observer = None

    def _process_new_lines(self) -> None:
        """Обрабатывает новые строки из лог-файла."""
        if not self.source_file.exists():
            return

        # Получаем текущий размер файла
        current_size = self.source_file.stat().st_size

        # Если файл был усечён (truncated) или ротирован, сбрасываем позицию
        if current_size < self._file_position:
            self._file_position = 0

        # Читаем новые строки
        if current_size > self._file_position:
            with self.source_file.open("r", encoding="utf-8") as f:
                f.seek(self._file_position)
                new_lines = f.readlines()

            # Записываем новые строки в целевой файл
            if self.target_file and new_lines:
                with self.target_file.open("a", encoding="utf-8") as f:
                    f.writelines(new_lines)

            # Обновляем позицию
            self._file_position = current_size
