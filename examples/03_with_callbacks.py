"""Пример 3: Использование callbacks.

Демонстрирует:
- Регистрацию callback функций
- Обработку событий в реальном времени
- Получение timestamp и event_id
- Множественные callbacks
"""

import time
from datetime import datetime
from pathlib import Path

from log_interceptor import LogInterceptor

source_file = Path("app.log")
source_file.touch()

# Счетчики для статистики
error_count = 0
warning_count = 0
all_events = []


def on_error(line: str, timestamp: float, event_id: int) -> None:
    """Callback для обработки ошибок."""
    global error_count
    if "ERROR" in line:
        error_count += 1
        dt = datetime.fromtimestamp(timestamp)
        print(f"[ERROR #{error_count}] {dt.strftime('%H:%M:%S')}: {line.strip()}")


def on_warning(line: str, timestamp: float, event_id: int) -> None:
    """Callback для обработки предупреждений."""
    global warning_count
    if "WARNING" in line:
        warning_count += 1
        print(f"[WARNING #{warning_count}]: {line.strip()}")


def collect_all(line: str, timestamp: float, event_id: int) -> None:
    """Callback для сбора всех событий."""
    all_events.append({
        "event_id": event_id,
        "timestamp": timestamp,
        "line": line.strip()
    })


print("=== Callbacks в действии ===\n")

# Создаем interceptor и регистрируем callbacks
interceptor = LogInterceptor(source_file=source_file, use_buffer=True)
interceptor.add_callback(on_error)
interceptor.add_callback(on_warning)
interceptor.add_callback(collect_all)

interceptor.start()

# Симулируем логи
print("Генерируем логи...\n")
with source_file.open("w") as f:
    f.write("INFO: Application started\n")
    time.sleep(0.1)

    f.write("ERROR: Failed to connect\n")
    f.flush()
    time.sleep(0.2)

    f.write("WARNING: Retrying connection\n")
    f.flush()
    time.sleep(0.2)

    f.write("INFO: Connection established\n")
    f.flush()
    time.sleep(0.1)

    f.write("ERROR: Invalid data format\n")
    f.flush()
    time.sleep(0.2)

    f.write("WARNING: Using default value\n")
    f.flush()
    time.sleep(0.2)

interceptor.stop()

# Статистика
print("\n=== Статистика ===")
print(f"Всего событий: {len(all_events)}")
print(f"Ошибок: {error_count}")
print(f"Предупреждений: {warning_count}")

# Показать все события с метаданными
print("\n=== Все события ===")
for event in all_events:
    dt = datetime.fromtimestamp(event["timestamp"])
    print(f"[{event['event_id']}] {dt.strftime('%H:%M:%S.%f')[:-3]} - {event['line']}")

# Пример: удаление callback
print("\n=== Удаление callback ===")
interceptor.remove_callback(on_error)
interceptor.remove_callback(on_warning)
interceptor.remove_callback(collect_all)

error_count = 0
warning_count = 0
all_events.clear()

interceptor.start()

with source_file.open("a") as f:
    f.write("ERROR: This should not trigger callbacks\n")
    f.flush()
    time.sleep(0.2)

interceptor.stop()

print(f"Ошибок после удаления: {error_count} (должно быть 0)")
print(f"Всего событий после удаления: {len(all_events)} (должно быть 0)")

# Cleanup
source_file.unlink()

print("\n✅ Пример завершен!")

