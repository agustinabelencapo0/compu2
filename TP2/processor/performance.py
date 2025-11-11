from __future__ import annotations

import time
import urllib.request


def analyze_performance(url: str) -> dict:
    # Medición simplificada: una sola request a la URL principal
    start = time.perf_counter()
    with urllib.request.urlopen(url, timeout=30) as resp:
        data = resp.read()
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    size_kb = int(len(data) / 1024)
    return {
        "load_time_ms": max(1, elapsed_ms),
        "total_size_kb": size_kb,
        "num_requests": 1,
    }

