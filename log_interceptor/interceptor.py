"""Основной модуль LogInterceptor для мониторинга и перехвата лог-файлов.

Предоставляет класс LogInterceptor для отслеживания изменений в лог-файлах
в реальном времени с использованием watchdog.
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
    """Метаданные для строки лога."""

    line: str
    timestamp: float
    event_id: int

# Тип для callback функций
CallbackType = Callable[[str, float, int], None]

# Настраиваем логгер для внутренних ошибок
logger = logging.getLogger(__name__)


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
        """Инициализирует LogInterceptor.

        Args:
            source_file: Путь к исходному лог-файлу для мониторинга.
            target_file: Путь к целевому файлу для записи захваченных строк.
            allow_missing: Если True, не требует существования файла при инициализации.
            use_buffer: Если True, включает буферизацию строк в памяти.
            buffer_size: Максимальный размер буфера в памяти.
            overflow_strategy: Стратегия при переполнении буфера ("FIFO").
            filters: Список фильтров для применения к новым строкам.
            config: Объект конфигурации для расширенных настроек.
            add_timestamps: Если True, добавляет ISO 8601 timestamp к строкам в target_file.

        Raises:
            FileNotFoundError: Если source_file не существует и allow_missing=False.

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

        # Статистика
        self._lines_captured = 0
        self._events_processed = 0
        self._start_time: float | None = None

        # Сохраняем конфигурацию или используем значения по умолчанию
        if config:
            from log_interceptor.config import InterceptorConfig  # noqa: PLC0415

            self._config = config
        else:
            from log_interceptor.config import InterceptorConfig  # noqa: PLC0415

            self._config = InterceptorConfig()

        # Инициализируем буфер в памяти
        self._buffer: deque[str] | None = deque(maxlen=buffer_size) if use_buffer else None
        self._buffer_lock = threading.Lock()
        self._overflow_strategy = overflow_strategy

        # Инициализируем буфер метаданных
        self._metadata_buffer: deque[LineMetadata] = deque(maxlen=buffer_size)
        self._metadata_lock = threading.Lock()

        # Инициализируем фильтры
        self._filters: Sequence[BaseFilter] = filters if filters else []

        # Инициализируем callback систему
        self._callbacks: list[CallbackType] = []
        self._callbacks_lock = threading.Lock()
        self._event_counter = 0

        # Настройки timestamp
        self._add_timestamps = add_timestamps

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
        self._start_time = time.time()

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

    def get_buffered_lines(self) -> Sequence[str]:
        """Возвращает текущее содержимое буфера в памяти.

        Returns:
            Список строк из буфера. Пустой список, если буферизация не включена.

        """
        if not self._buffer:
            return []
        with self._buffer_lock:
            return list(self._buffer)

    def clear_buffer(self) -> None:
        """Очищает буфер в памяти.

        Удаляет все строки из буфера. Если буферизация не включена, ничего не делает.

        """
        if not self._buffer:
            return
        with self._buffer_lock:
            self._buffer.clear()

    def get_lines_with_metadata(self) -> list[LineMetadata]:
        """Возвращает список строк с метаданными.

        Returns:
            Список словарей с ключами: line, timestamp, event_id.

        """
        with self._metadata_lock:
            return list(self._metadata_buffer)

    def pause(self) -> None:
        """Приостанавливает захват новых строк без остановки watchdog."""
        self._paused = True

    def resume(self) -> None:
        """Возобновляет захват новых строк после паузы."""
        self._paused = False

    def is_paused(self) -> bool:
        """Проверяет, находится ли interceptor на паузе.

        Returns:
            True, если на паузе, иначе False.

        """
        return self._paused

    def get_stats(self) -> dict[str, int | float]:
        """Возвращает статистику работы interceptor.

        Returns:
            Словарь со статистикой: lines_captured, events_processed, start_time, uptime_seconds.

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
        """Добавляет callback функцию для уведомления о новых строках.

        Args:
            callback: Функция с сигнатурой (line: str, timestamp: float, event_id: int) -> None

        """
        with self._callbacks_lock:
            if callback not in self._callbacks:
                self._callbacks.append(callback)

    def remove_callback(self, callback: CallbackType) -> None:
        """Удаляет callback функцию из списка.

        Args:
            callback: Функция для удаления.

        """
        with self._callbacks_lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)

    def __enter__(self) -> Self:
        """Вход в context manager.

        Автоматически запускает мониторинг.

        Returns:
            Экземпляр LogInterceptor.

        """
        self.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        """Выход из context manager.

        Автоматически останавливает мониторинг и освобождает ресурсы.

        Args:
            exc_type: Тип исключения (если было).
            exc_val: Значение исключения (если было).
            exc_tb: Traceback исключения (если было).

        """
        self.stop()

    def _invoke_callbacks(self, line: str, timestamp: float, event_id: int) -> None:
        """Вызывает все зарегистрированные callbacks для строки лога.

        Args:
            line: Строка лога для передачи в callbacks.
            timestamp: Временная метка события.
            event_id: Уникальный идентификатор события.

        """
        if not self._callbacks:
            return

        # Копируем список callbacks под блокировкой
        with self._callbacks_lock:
            callbacks_copy = self._callbacks.copy()

        # Вызываем callbacks вне блокировки
        for callback in callbacks_copy:
            try:
                callback(line, timestamp, event_id)
            except Exception:  # noqa: PERF203
                # Логируем ошибку, но не прерываем обработку
                logger.exception("Error in callback %s", callback.__name__)

    def _apply_filters(self, line: str) -> bool:
        """Применяет фильтры к строке лога.

        Args:
            line: Строка для фильтрации.

        Returns:
            True, если строка прошла все фильтры, иначе False.

        """
        if not self._filters:
            return True

        # Применяем все фильтры (логика AND)
        return all(filter_obj.filter(line) for filter_obj in self._filters)

    def _process_new_lines(self) -> None:  # noqa: C901, PLR0912
        """Обрабатывает новые строки из лог-файла с обработкой ошибок."""
        try:
            if not self.source_file.exists():
                return

            # Если на паузе, обновляем позицию но не обрабатываем строки
            if self._paused:
                current_size = self.source_file.stat().st_size
                self._file_position = current_size
                return

            # Получаем текущий размер файла
            current_size = self.source_file.stat().st_size

            # Если файл был усечён (truncated) или ротирован, сбрасываем позицию
            if current_size < self._file_position:
                logger.info("File rotation detected for %s, resetting position", self.source_file)
                self._file_position = 0

            # Читаем новые строки
            if current_size > self._file_position:
                with self.source_file.open("r", encoding=self._config.encoding) as f:
                    f.seek(self._file_position)
                    new_lines = f.readlines()

                # Применяем фильтры к строкам
                filtered_lines = [line for line in new_lines if self._apply_filters(line)]

                # Увеличиваем счетчики
                if filtered_lines:
                    self._lines_captured += len(filtered_lines)
                    self._events_processed += 1

                # Обрабатываем каждую отфильтрованную строку
                for line in filtered_lines:
                    # Получаем метаданные
                    timestamp = time.time()
                    event_id = self._event_counter
                    self._event_counter += 1

                    # Сохраняем метаданные
                    metadata: LineMetadata = {
                        "line": line.rstrip("\n"),
                        "timestamp": timestamp,
                        "event_id": event_id,
                    }
                    with self._metadata_lock:
                        self._metadata_buffer.append(metadata)

                    # Записываем в буфер (если включён)
                    if self._buffer is not None:
                        with self._buffer_lock:
                            self._buffer.append(line)

                    # Вызываем callbacks
                    self._invoke_callbacks(line, timestamp, event_id)

                # Записываем отфильтрованные строки в целевой файл
                if self.target_file and filtered_lines:
                    with self.target_file.open("a", encoding=self._config.encoding) as f:
                        for line in filtered_lines:
                            if self._add_timestamps:
                                # Форматируем timestamp в ISO 8601
                                dt = datetime.fromtimestamp(time.time(), tz=timezone.utc)
                                timestamp_str = dt.isoformat()
                                f.write(f"[CAPTURED_AT: {timestamp_str}] {line}")
                            else:
                                f.write(line)

                # Обновляем позицию
                self._file_position = current_size

        except PermissionError:
            logger.warning("Permission denied when reading %s, will retry", self.source_file)
        except OSError:
            logger.exception("OS error when reading %s", self.source_file)
        except Exception:
            logger.exception("Unexpected error processing %s", self.source_file)
