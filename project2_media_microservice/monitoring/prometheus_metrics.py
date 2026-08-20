"""Prometheus metrics for monitoring queue and worker stats"""
import time
from functools import wraps

metrics = {
    "jobs_total": 0,
    "jobs_completed": 0,
    "jobs_failed": 0,
    "processing_time_ms": [],
    "queue_length": 0
}


def track_job(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        metrics["jobs_total"] += 1
        start = time.time()
        try:
            result = func(*args, **kwargs)
            metrics["jobs_completed"] += 1
            return result
        except Exception as e:
            metrics["jobs_failed"] += 1
            raise
        finally:
            elapsed = (time.time() - start) * 1000
            metrics["processing_time_ms"].append(elapsed)
    return wrapper


def get_metrics():
    avg_time = sum(metrics["processing_time_ms"][-100:]) / max(len(metrics["processing_time_ms"][-100:]), 1)
    return {
        "jobs_total": metrics["jobs_total"],
        "jobs_completed": metrics["jobs_completed"],
        "jobs_failed": metrics["jobs_failed"],
        "avg_processing_time_ms": round(avg_time, 2),
        "queue_length": metrics["queue_length"]
    }
