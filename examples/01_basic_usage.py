"""Пример 1: Базовое использование LogInterceptor.

Демонстрирует:
- Простейший сценарий захвата логов
- Использование context manager
- Запись в target_file
"""

import time
from pathlib import Path

from log_interceptor import LogInterceptor

# Создаем временные файлы
source_file = Path("app.log")
target_file = Path("captured.log")

# Создаем исходный файл
source_file.touch()

# Вариант 1: Context Manager (рекомендуется)
print("=== Context Manager ===")
with LogInterceptor(
    source_file=source_file,
    target_file=target_file
) as interceptor:
    print(f"Interceptor запущен: {interceptor.is_running()}")

    # Симулируем запись логов
    with source_file.open("a") as f:
        f.write("INFO: Application started\n")
        f.write("DEBUG: Loading configuration\n")
        f.write("INFO: Server listening on port 8080\n")

    time.sleep(0.5)  # Даем время на обработку

print(f"Interceptor остановлен: {interceptor.is_running()}")

# Проверяем результат
if target_file.exists():
    print("\n=== Захваченные логи ===")
    print(target_file.read_text())

# Вариант 2: Явное управление
print("\n=== Явное управление ===")
interceptor = LogInterceptor(
    source_file=source_file,
    target_file=target_file
)

interceptor.start()
print(f"Interceptor запущен: {interceptor.is_running()}")

# Симулируем еще логи
with source_file.open("a") as f:
    f.write("WARNING: High memory usage\n")
    f.write("INFO: Request processed\n")

time.sleep(0.5)

interceptor.stop()
print(f"Interceptor остановлен: {interceptor.is_running()}")

# Cleanup
source_file.unlink()
target_file.unlink()

print("\n✅ Пример завершен!")

