"""Example 1: Basic LogInterceptor usage.

Demonstrates:
- Simplest log capture scenario
- Using context manager
- Writing to target_file
"""

import time
from pathlib import Path

from log_interceptor import LogInterceptor

# Create temporary files
source_file = Path("app.log")
target_file = Path("captured.log")

# Create source file
source_file.touch()

# Option 1: Context Manager (recommended)
print("=== Context Manager ===")
with LogInterceptor(
    source_file=source_file,
    target_file=target_file
) as interceptor:
    print(f"Interceptor running: {interceptor.is_running()}")

    # Simulate log writing
    with source_file.open("a") as f:
        f.write("INFO: Application started\n")
        f.write("DEBUG: Loading configuration\n")
        f.write("INFO: Server listening on port 8080\n")

    time.sleep(0.5)  # Give time for processing

print(f"Interceptor stopped: {interceptor.is_running()}")

# Check result
if target_file.exists():
    print("\n=== Captured Logs ===")
    print(target_file.read_text())

# Option 2: Explicit management
print("\n=== Explicit Management ===")
interceptor = LogInterceptor(
    source_file=source_file,
    target_file=target_file
)

interceptor.start()
print(f"Interceptor running: {interceptor.is_running()}")

# Simulate more logs
with source_file.open("a") as f:
    f.write("WARNING: High memory usage\n")
    f.write("INFO: Request processed\n")

time.sleep(0.5)

interceptor.stop()
print(f"Interceptor stopped: {interceptor.is_running()}")

# Cleanup
source_file.unlink()
target_file.unlink()

print("\n✅ Example completed!")
