# hooks/no_console_qprocess.py
# Force all QProcess instances to spawn child processes with CREATE_NO_WINDOW.

# Allow opt-out for troubleshooting:
if os.environ.get("ALLOW_CONSOLE_CHILD") not in ("1", "true", "True"):
    try:
        from PyQt6.QtCore import QProcess
    except Exception:
        QProcess = None

    if QProcess is not None:
        CREATE_NO_WINDOW = 0x08000000

        # Modifier that Qt calls prior to CreateProcess on Windows
        def _modifier(args):
            try:
                # PyQt6 exposes creationFlags; OR-in CREATE_NO_WINDOW
                args.creationFlags |= CREATE_NO_WINDOW
            except Exception:
                pass

        # Monkey-patch QProcess.__init__ so every instance gets our modifier
        _orig_init = QProcess.__init__

        def _init(self, *a, **k):
            _orig_init(self, *a, **k)
            try:
                # Install modifier once per instance
                self.setCreateProcessArgumentsModifier(_modifier)
            except Exception:
                pass

        QProcess.__init__ = _init