"""Helpers for tracking memory usage."""

import psutil

def get_memory_usage():
    """Displays current memory usage."""
    pid = psutil.Process()

    memory_info = pid.memory_info()

    return memory_info.rss / (1024 * 1024)  # Convert to MB
