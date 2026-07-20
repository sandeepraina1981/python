# hooks/no_console_subprocess.py
# Suppress transient console windows for child processes on Windows
import os
import sys

if sys.platform.startswith("win"):
    import subprocess

    CREATE_NO_WINDOW = 0x08000000

    _orig_popen = subprocess.Popen

    def _patched_popen(*args, **kwargs):
        # Respect explicit caller intent: if creationflags provided, don't override.
        if "creationflags" not in kwargs:
            kwargs["creationflags"] = CREATE_NO_WINDOW
        # Avoid inheriting any console handles
        kwargs.setdefault("stdin", subprocess.DEVNULL)
        # Keep outputs from forcing a console; callers can still change these.
        kwargs.setdefault("stdout", subprocess.PIPE)
        kwargs.setdefault("stderr", subprocess.PIPE)
        # Prefer shell=False unless caller asked for shell=True
        # (Do NOT force it; some commands require shell=True)
        return _orig_popen(*args, **kwargs)

    subprocess.Popen = _patched_popen