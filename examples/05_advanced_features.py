"""Пример 5: Продвинутые возможности.

Демонстрирует:
- Pause/Resume для контроля потока
- Статистику и метаданные
- Timestamp в файлах
- Конфигурацию
"""

import time
from datetime import datetime
from pathlib import Path

from log_interceptor import InterceptorConfig, LogInterceptor

source_file = Path("app.log")
target_file = Path("captured.log")
source_file.touch()

# Пример 1: Pause/Resume для пакетной обработки
print("=== Пример 1: Pause/Resume ===\n")

interceptor = LogInterceptor(
    source_file=source_file,
    use_buffer=True,
    buffer_size=100
)
interceptor.start()

print("Начинаем мониторинг...")

for batch in range(3):
    print(f"\nБатч {batch + 1}:")

    # Генерируем логи
    with source_file.open("a") as f:
        for i in range(5):
            f.write(f"INFO: Batch {batch + 1}, Entry {i + 1}\n")
            f.flush()

    time.sleep(0.3)

    # Приостанавливаем для обработки
    interceptor.pause()
    print(f"  Пауза для обработки (is_paused={interceptor.is_paused()})")

    # Получаем и обрабатываем буфер
    lines = interceptor.get_buffered_lines()
    print(f"  Обработано: {len(lines)} строк")

    # Очищаем буфер
    interceptor.clear_buffer()

    # Возобновляем
    interceptor.resume()
    print(f"  Возобновлено (is_paused={interceptor.is_paused()})")

interceptor.stop()

# Пример 2: Статистика
print("\n=== Пример 2: Статистика ===\n")

interceptor = LogInterceptor(
    source_file=source_file,
    use_buffer=True
)
interceptor.start()

# Генерируем активность
with source_file.open("a") as f:
    for i in range(50):
        f.write(f"INFO: Event {i + 1}\n")
        if i % 10 == 0:
            f.flush()
            time.sleep(0.1)

time.sleep(0.5)

# Получаем статистику
stats = interceptor.get_stats()
print(f"Захвачено строк: {stats['lines_captured']}")
print(f"Обработано событий: {stats['events_processed']}")
print(f"Время работы: {stats['uptime_seconds']:.2f}s")

start_time = datetime.fromtimestamp(stats["start_time"])
print(f"Запущен в: {start_time.strftime('%H:%M:%S')}")

interceptor.stop()

# Пример 3: Метаданные
print("\n=== Пример 3: Метаданные ===\n")

interceptor = LogInterceptor(
    source_file=source_file,
    use_buffer=True
)
interceptor.start()

# Важные события
with source_file.open("a") as f:
    f.write("INFO: User login: john@example.com\n")
    time.sleep(0.1)
    f.write("INFO: Payment processed: $99.99\n")
    time.sleep(0.1)
    f.write("INFO: User logout\n")
    f.flush()

time.sleep(0.3)

# Получаем метаданные для аудита
metadata = interceptor.get_lines_with_metadata()
print(f"Всего событий: {len(metadata)}\n")

for entry in metadata:
    dt = datetime.fromtimestamp(entry["timestamp"])
    print(f"Event ID: {entry['event_id']}")
    print(f"  Time: {dt.strftime('%H:%M:%S.%f')[:-3]}")
    print(f"  Line: {entry['line']}")
    print()

interceptor.stop()

# Пример 4: Timestamp в файлах
print("=== Пример 4: Timestamp в файлах ===\n")

with LogInterceptor(
    source_file=source_file,
    target_file=target_file,
    add_timestamps=True  # Добавляем ISO 8601 timestamp
) as interceptor:
    with source_file.open("a") as f:
        f.write("ERROR: Critical system error\n")
        f.write("WARNING: Resource limit reached\n")

    time.sleep(0.5)

# Показываем результат
print("Captured file content:")
print(target_file.read_text())

# Пример 5: Конфигурация
print("\n=== Пример 5: Конфигурация ===\n")

# Aggressive preset для высоконагруженных систем
config = InterceptorConfig.from_preset("aggressive")
print("Aggressive config:")
print(f"  debounce_interval: {config.debounce_interval}")
print(f"  buffer_size: {config.buffer_size}")

# Conservative preset для низкоприоритетных задач
config = InterceptorConfig.from_preset("conservative")
print("\nConservative config:")
print(f"  debounce_interval: {config.debounce_interval}")
print(f"  buffer_size: {config.buffer_size}")

# Кастомная конфигурация
config = InterceptorConfig(
    buffer_size=10000,
    encoding="utf-8",
    retry_max_attempts=10
)
print("\nCustom config:")
print(f"  buffer_size: {config.buffer_size}")
print(f"  encoding: {config.encoding}")
print(f"  retry_max_attempts: {config.retry_max_attempts}")

# Cleanup
source_file.unlink()
if target_file.exists():
    target_file.unlink()

print("\n✅ Пример завершен!")

