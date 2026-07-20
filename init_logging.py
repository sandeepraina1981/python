# hooks/init_logging.py
"""
Runtime hook: initialize application logging (file-only) and crash capture.
- File name includes date/time (and PID) so each run gets its own log:
  e.g., app_2026-03-04_11-44-07_1234.log
- No console handlers (GUI-safe).
- Rotating file logs to avoid unbounded growth.
- Captures unhandled exceptions from sys, threading, asyncio.
- Adds faulthandler to dump tracebacks on hard crashes (signals).
- Safe fallbacks if the preferred log path is not writable.
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime

APP_FRIENDLY_NAME = "Lenze Service Tool"

def _safe_log_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("APPDATA") or str(Path.home())
    base_path = Path(base) if base else Path.cwd()
    log_dir = base_path / APP_FRIENDLY_NAME / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        test_file = log_dir / ".write_test"
        with test_file.open("w", encoding="utf-8") as f:
            f.write("ok")
        test_file.unlink(missing_ok=True)
        return log_dir
    except Exception:
        log_dir = Path.cwd() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

def _timestamped_log_path(log_dir: Path) -> Path:
    # Example: app_2026-03-04_11-44-07_1234.log
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    pid = os.getpid()
    return log_dir / f"app_{ts}_{pid}.log"

def _configure_logging() -> Path:
    log_dir = _safe_log_dir()
    log_file = _timestamped_log_path(log_dir)

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Avoid duplicate handlers if the hook is re-imported
    has_rotating = any(isinstance(h, RotatingFileHandler) for h in root.handlers)
    if not has_rotating:
        handler = RotatingFileHandler(
            log_file, maxBytes=2_000_000, backupCount=5, encoding="utf-8"
        )
        fmt = logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s [%(process)d:%(threadName)s] %(message)s"
        )
        handler.setFormatter(fmt)
        root.addHandler(handler)

        # Tame noisy libs if necessary
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)

    return log_file

def _install_crash_handlers():
    # Main thread: sys.excepthook
    def _sys_except_hook(exc_type, exc, tb):
        logging.critical("Unhandled exception", exc_info=(exc_type, exc, tb))
        # Let the process exit naturally.

    sys.excepthook = _sys_except_hook

    # Threads (Py 3.8+)
    try:
        import threading
        if hasattr(threading, "excepthook"):
            def _thread_except_hook(args):
                logging.critical(
                    "Unhandled thread exception (thread=%s)",
                    getattr(args, "thread", None),
                    exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
                )
            threading.excepthook = _thread_except_hook
    except Exception:
        pass

    # asyncio tasks
    try:
        import asyncio
        def _asyncio_handler(loop, context):
            msg = context.get("message") or "Unhandled asyncio exception"
            exc = context.get("exception")
            if exc:
                logging.critical("%s", msg, exc_info=exc)
            else:
                logging.critical("%s | context=%s", msg, context)
        try:
            loop = asyncio.get_event_loop()
            loop.set_exception_handler(_asyncio_handler)
        except Exception:
            pass
    except Exception:
        pass

def _enable_faulthandler(log_file: Path):
    # Dump low-level crashes (segfaults etc.) to the same log file
    try:
        import faulthandler
        # Open in append-text mode; faulthandler expects a real file object
        f = open(log_file, "a", encoding="utf-8", buffering=1)
        try:
            faulthandler.enable(file=f)
            # Optional: also dump on timeout/deadlock scenarios you instrument yourself
            # faulthandler.dump_traceback_later(60, repeat=True, file=f)
        except Exception:
            f.close()
    except Exception:
        # Never break the app because of diagnostics
        pass

def _log_startup_banner(log_file: Path):
    try:
        import platform
        app_version = os.environ.get("APP_VERSION", "unknown")
        logging.info("=== %s started ===", APP_FRIENDLY_NAME)
        logging.info("Version: %s", app_version)
        logging.info("Python: %s", platform.python_version())
        logging.info("Executable: %s", sys.executable)
        logging.info("CWD: %s", Path.cwd())
        logging.info("Log file: %s", log_file)
    except Exception:
        pass

def _main():
    log_file = _configure_logging()
    _enable_faulthandler(log_file)
    _install_crash_handlers()
    _log_startup_banner(log_file)

_main()