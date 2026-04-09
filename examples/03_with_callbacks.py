"""Example 3: Using callbacks.

Demonstrates:
- Registering callback functions
- Real-time event processing
- Getting timestamp and event_id
- Multiple callbacks
"""

import time
from datetime import datetime
from pathlib import Path

from log_interceptor import LogInterceptor

source_file = Path("app.log")
source_file.touch()

# Counters for statistics
error_count = 0
warning_count = 0
all_events = []


def on_error(line: str, timestamp: float, event_id: int) -> None:
    """Handle error callbacks."""
    global error_count
    if "ERROR" in line:
        error_count += 1
        dt = datetime.fromtimestamp(timestamp)
        print(f"[ERROR #{error_count}] {dt.strftime('%H:%M:%S')}: {line.strip()}")


def on_warning(line: str, timestamp: float, event_id: int) -> None:
    """Handle warning callbacks."""
    global warning_count
    if "WARNING" in line:
        warning_count += 1
        print(f"[WARNING #{warning_count}]: {line.strip()}")


def collect_all(line: str, timestamp: float, event_id: int) -> None:
    """Collect all events."""
    all_events.append({
        "event_id": event_id,
        "timestamp": timestamp,
        "line": line.strip()
    })


print("=== Callbacks in Action ===\n")

# Create interceptor and register callbacks
interceptor = LogInterceptor(source_file=source_file, use_buffer=True)
interceptor.add_callback(on_error)
interceptor.add_callback(on_warning)
interceptor.add_callback(collect_all)

interceptor.start()

# Simulate logs
print("Generating logs...\n")
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

# Statistics
print("\n=== Statistics ===")
print(f"Total events: {len(all_events)}")
print(f"Errors: {error_count}")
print(f"Warnings: {warning_count}")

# Show all events with metadata
print("\n=== All Events ===")
for event in all_events:
    dt = datetime.fromtimestamp(event["timestamp"])
    print(f"[{event['event_id']}] {dt.strftime('%H:%M:%S.%f')[:-3]} - {event['line']}")

# Example: removing callback
print("\n=== Removing Callback ===")
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

print(f"Errors after removal: {error_count} (should be 0)")
print(f"Total events after removal: {len(all_events)} (should be 0)")

# Cleanup
source_file.unlink()

print("\n✅ Example completed!")

