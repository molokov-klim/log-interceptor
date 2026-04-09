"""Example 5: Advanced features.

Demonstrates:
- Pause/Resume for flow control
- Statistics and metadata
- Timestamps in files
- Configuration
"""

import time
from datetime import datetime
from pathlib import Path

from log_interceptor import InterceptorConfig, LogInterceptor

source_file = Path("app.log")
target_file = Path("captured.log")
source_file.touch()

# Example 1: Pause/Resume for batch processing
print("=== Example 1: Pause/Resume ===\n")

interceptor = LogInterceptor(
    source_file=source_file,
    use_buffer=True,
    buffer_size=100
)
interceptor.start()

print("Starting monitoring...")

for batch in range(3):
    print(f"\nBatch {batch + 1}:")

    # Generate logs
    with source_file.open("a") as f:
        for i in range(5):
            f.write(f"INFO: Batch {batch + 1}, Entry {i + 1}\n")
            f.flush()

    time.sleep(0.3)

    # Pause for processing
    interceptor.pause()
    print(f"  Pause for processing (is_paused={interceptor.is_paused()})")

    # Get and process buffer
    lines = interceptor.get_buffered_lines()
    print(f"  Processed: {len(lines)} lines")

    # Clear buffer
    interceptor.clear_buffer()

    # Resume
    interceptor.resume()
    print(f"  Resumed (is_paused={interceptor.is_paused()})")

interceptor.stop()

# Example 2: Statistics
print("\n=== Example 2: Statistics ===\n")

interceptor = LogInterceptor(
    source_file=source_file,
    use_buffer=True
)
interceptor.start()

# Generate activity
with source_file.open("a") as f:
    for i in range(50):
        f.write(f"INFO: Event {i + 1}\n")
        if i % 10 == 0:
            f.flush()
            time.sleep(0.1)

time.sleep(0.5)

# Get statistics
stats = interceptor.get_stats()
print(f"Captured lines: {stats['lines_captured']}")
print(f"Events processed: {stats['events_processed']}")
print(f"Uptime: {stats['uptime_seconds']:.2f}s")

start_time = datetime.fromtimestamp(stats["start_time"])
print(f"Started at: {start_time.strftime('%H:%M:%S')}")

interceptor.stop()

# Example 3: Metadata
print("\n=== Example 3: Metadata ===\n")

interceptor = LogInterceptor(
    source_file=source_file,
    use_buffer=True
)
interceptor.start()

# Important events
with source_file.open("a") as f:
    f.write("INFO: User login: john@example.com\n")
    time.sleep(0.1)
    f.write("INFO: Payment processed: $99.99\n")
    time.sleep(0.1)
    f.write("INFO: User logout\n")
    f.flush()

time.sleep(0.3)

# Get metadata for audit
metadata = interceptor.get_lines_with_metadata()
print(f"Total events: {len(metadata)}\n")

for entry in metadata:
    dt = datetime.fromtimestamp(entry["timestamp"])
    print(f"Event ID: {entry['event_id']}")
    print(f"  Time: {dt.strftime('%H:%M:%S.%f')[:-3]}")
    print(f"  Line: {entry['line']}")
    print()

interceptor.stop()

# Example 4: Timestamps in files
print("=== Example 4: Timestamps in Files ===\n")

with LogInterceptor(
    source_file=source_file,
    target_file=target_file,
    add_timestamps=True  # Add ISO 8601 timestamp
) as interceptor:
    with source_file.open("a") as f:
        f.write("ERROR: Critical system error\n")
        f.write("WARNING: Resource limit reached\n")

    time.sleep(0.5)

# Show result
print("Captured file content:")
print(target_file.read_text())

# Example 5: Configuration
print("\n=== Example 5: Configuration ===\n")

# Aggressive preset for high-load systems
config = InterceptorConfig.from_preset("aggressive")
print("Aggressive config:")
print(f"  debounce_interval: {config.debounce_interval}")
print(f"  buffer_size: {config.buffer_size}")

# Conservative preset for low-priority tasks
config = InterceptorConfig.from_preset("conservative")
print("\nConservative config:")
print(f"  debounce_interval: {config.debounce_interval}")
print(f"  buffer_size: {config.buffer_size}")

# Custom configuration
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

print("\n✅ Example completed!")

