"""Small, versioned user preferences; scan results remain session-only."""

import json
import os
from pathlib import Path
import sys
import tempfile


def settings_path():
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", str(Path.home())))
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config")))
    return base / "PiNT" / "settings.json"


class AppSettings:
    LIMITS = {"port_timeout": (5, 120), "mdns_timeout": (5, 120),
              "monitor_poll_ms": (1000, 30000)}

    def __init__(self, path=None):
        self._path = Path(path) if path is not None else settings_path()
        self.port_timeout = 30
        self.mdns_timeout = 30
        self.monitor_poll_ms = 2000
        try:
            values = json.loads(self._path.read_text(encoding="utf-8"))
            if not isinstance(values, dict):
                return
            for name, (low, high) in self.LIMITS.items():
                value = values.get(name)
                if type(value) is int and low <= value <= high:
                    setattr(self, name, value)
        except (OSError, ValueError):
            pass

    def save(self):
        values = {name: getattr(self, name) for name in self.LIMITS}
        values["version"] = 1
        self._path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False,
                                             dir=self._path.parent, suffix=".tmp") as f:
                temp_path = Path(f.name)
                json.dump(values, f, indent=2)
                f.write("\n")
            os.replace(temp_path, self._path)
        finally:
            if temp_path is not None:
                temp_path.unlink(missing_ok=True)
