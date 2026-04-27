import os
import traceback
from datetime import datetime
from typing import Optional

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _ensure_logs_dir() -> str:
    logs_dir = os.path.join(_PROJECT_ROOT, "logs")
    try:
        os.makedirs(logs_dir, exist_ok=True)
    except OSError:
        pass
    return logs_dir


def _make_log_name(test_object: str, test_component: str) -> str:
    return f"{test_object}-{test_component}-debug.log"


def get_log_path(test_object: str, test_component: str) -> str:
    return os.path.join(_ensure_logs_dir(), _make_log_name(test_object, test_component))


def write_log(test_object: str, test_component: str, message: str) -> None:
    try:
        log_path = get_log_path(test_object, test_component)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}] {message}\n")
    except Exception:
        pass


def log_crash(test_object: str, test_component: str, crash_report: str) -> None:
    try:
        log_path = get_log_path(test_object, test_component)
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"Crash Report - {datetime.now()}\n")
            f.write(f"{'-' * 30}\n")
            f.write(crash_report)
            f.write(f"{'=' * 30}\n\n")
    except Exception:
        pass


class CrashLogger:
    def __init__(self, test_object: str, test_component: str):
        self.test_object = test_object
        self.test_component = test_component
        self.log_path = get_log_path(test_object, test_component)

    def write(self, message: str) -> None:
        write_log(self.test_object, self.test_component, message)

    def log_exception(self, exc: Exception, context: str = "") -> None:
        msg = f"EXCEPTION in {context}: {type(exc).__name__}: {exc}\n{traceback.format_exc()}"
        self.write(msg)

    def log_crash(self, crash_report: str) -> None:
        log_crash(self.test_object, self.test_component, crash_report)


class WorkerLogger:
    def __init__(self):
        self.logs_dir = _ensure_logs_dir()
        self.lifecycle_path = os.path.join(self.logs_dir, "performance-workers-lifecycle-debug.log")
        self.render_path = os.path.join(self.logs_dir, "performance-rendering-debug.log")
        self.ui_access_path = os.path.join(self.logs_dir, "performance-ui-access-debug.log")
        self.error_path = os.path.join(self.logs_dir, "performance-error-runtime-debug.log")

    def log_lifecycle(self, thread_name: str, message: str) -> None:
        try:
            with open(self.lifecycle_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y%m%d %H:%M:%S.%f')[:-3]}] TID= {message}\n")
                f.flush()
        except Exception:
            pass

    def log_render(self, message: str) -> None:
        try:
            with open(self.render_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y%m%d %H:%M:%S.%f')[:-3]}] {message}\n")
                f.flush()
        except Exception:
            pass

    def log_ui_access(self, message: str) -> None:
        try:
            with open(self.ui_access_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y%m%d %H:%M:%S.%f')[:-3]}] {message}\n")
                f.flush()
        except Exception:
            pass

    def log_error(self, context: str, tb: str) -> None:
        try:
            with open(self.error_path, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now().strftime('%Y%m%d %H:%M:%S.%f')[:-3]}] {context} ERROR:\n{tb}\n")
                f.flush()
        except Exception:
            pass


_worker_logger: Optional[WorkerLogger] = None


def get_worker_logger() -> WorkerLogger:
    global _worker_logger
    if _worker_logger is None:
        _worker_logger = WorkerLogger()
    return _worker_logger


_global_crash_log_path = os.path.join(_ensure_logs_dir(), "mw_crash-debug.log")


def get_crash_log_path() -> str:
    return _global_crash_log_path


def log_global_crash(crash_report: str) -> None:
    log_crash("mw", "crash", crash_report)