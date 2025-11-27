"""Пример 2: Использование фильтров.

Демонстрирует:
- RegexFilter для фильтрации по паттерну
- Whitelist и blacklist режимы
- CompositeFilter для комбинации фильтров
- Буферизация в памяти
"""

import time
from pathlib import Path

from log_interceptor import LogInterceptor
from log_interceptor.filters import CompositeFilter, PredicateFilter, RegexFilter

source_file = Path("app.log")
source_file.touch()

# Симулируем разные типы логов
with source_file.open("w") as f:
    f.write("INFO: Application started\n")
    f.write("DEBUG: Loading module A\n")
    f.write("ERROR: Failed to connect to database\n")
    f.write("DEBUG: Loading module B\n")
    f.write("WARNING: Retrying connection\n")
    f.write("INFO: Connection established\n")
    f.write("ERROR: Invalid user input\n")
    f.write("CRITICAL: System overload\n")

# Пример 1: Только ERROR строки
print("=== Пример 1: Только ERROR ===")
error_filter = RegexFilter(r"ERROR", mode="whitelist")

with LogInterceptor(
    source_file=source_file,
    filters=[error_filter],
    use_buffer=True
) as interceptor:
    time.sleep(0.5)

    lines = interceptor.get_buffered_lines()
    print(f"Захвачено строк: {len(lines)}")
    for line in lines:
        print(f"  {line.strip()}")

# Пример 2: Исключить DEBUG
print("\n=== Пример 2: Без DEBUG ===")
no_debug = RegexFilter(r"DEBUG", mode="blacklist")

with LogInterceptor(
    source_file=source_file,
    filters=[no_debug],
    use_buffer=True
) as interceptor:
    time.sleep(0.5)

    lines = interceptor.get_buffered_lines()
    print(f"Захвачено строк: {len(lines)}")
    for line in lines:
        print(f"  {line.strip()}")

# Пример 3: ERROR ИЛИ CRITICAL
print("\n=== Пример 3: ERROR или CRITICAL ===")
critical_filter = CompositeFilter([
    RegexFilter(r"ERROR"),
    RegexFilter(r"CRITICAL")
], mode="OR")

with LogInterceptor(
    source_file=source_file,
    filters=[critical_filter],
    use_buffer=True
) as interceptor:
    time.sleep(0.5)

    lines = interceptor.get_buffered_lines()
    print(f"Захвачено строк: {len(lines)}")
    for line in lines:
        print(f"  {line.strip()}")

# Пример 4: Комплексный фильтр
print("\n=== Пример 4: Комплексный фильтр ===")
complex_filter = CompositeFilter([
    # Должно быть ERROR, WARNING или CRITICAL
    CompositeFilter([
        RegexFilter(r"ERROR"),
        RegexFilter(r"WARNING"),
        RegexFilter(r"CRITICAL")
    ], mode="OR"),
    # И строка должна содержать больше 30 символов
    PredicateFilter(lambda line: len(line) > 30)
], mode="AND")

with LogInterceptor(
    source_file=source_file,
    filters=[complex_filter],
    use_buffer=True
) as interceptor:
    time.sleep(0.5)

    lines = interceptor.get_buffered_lines()
    print(f"Захвачено строк: {len(lines)}")
    for line in lines:
        print(f"  {line.strip()}")

# Cleanup
source_file.unlink()

print("\n✅ Пример завершен!")

