from __future__ import annotations
import random
import time

def jitter(mean: float, jitter_amt: float) -> float:
    if jitter_amt <= 0:
        return mean
    return max(0.0, random.gauss(mean, jitter_amt))

def sleep_ms(ms: float) -> None:
    if ms <= 0:
        return
    time.sleep(ms / 1000.0)
