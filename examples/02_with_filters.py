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

# Simulate different log types
with source_file.open("w") as f:
    f.write("INFO: Application started\n")
    f.write("DEBUG: Loading module A\n")
    f.write("ERROR: Failed to connect to database\n")
    f.write("DEBUG: Loading module B\n")
    f.write("WARNING: Retrying connection\n")
    f.write("INFO: Connection established\n")
    f.write("ERROR: Invalid user input\n")
    f.write("CRITICAL: System overload\n")

# Example 1: Only ERROR lines
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

# Example 2: Exclude DEBUG
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

# Example 3: ERROR OR CRITICAL
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

# Example 4: Complex filter
print("\n=== Пример 4: Комплексный фильтр ===")
complex_filter = CompositeFilter([
    # Must be ERROR, WARNING or CRITICAL
    CompositeFilter([
        RegexFilter(r"ERROR"),
        RegexFilter(r"WARNING"),
        RegexFilter(r"CRITICAL")
    ], mode="OR"),
    # And line must contain more than 30 characters
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

