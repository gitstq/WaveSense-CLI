"""
Logging Utilities
日志工具模块

Simple logging without external dependencies.
"""

import sys
from datetime import datetime
from typing import Optional


class Logger:
    """Simple console logger"""

    LEVELS = {
        "DEBUG": 0,
        "INFO": 1,
        "WARNING": 2,
        "ERROR": 3
    }

    def __init__(self, name: str = "WaveSense", level: str = "INFO"):
        self.name = name
        self.level = self.LEVELS.get(level, 1)

    def _log(self, level: str, message: str) -> None:
        """Internal log method"""
        if self.LEVELS.get(level, 1) < self.level:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        output = f"[{timestamp}] [{level}] [{self.name}] {message}"

        if level == "ERROR":
            sys.stderr.write(output + "\n")
            sys.stderr.flush()
        else:
            sys.stdout.write(output + "\n")
            sys.stdout.flush()

    def debug(self, message: str) -> None:
        self._log("DEBUG", message)

    def info(self, message: str) -> None:
        self._log("INFO", message)

    def warning(self, message: str) -> None:
        self._log("WARNING", message)

    def error(self, message: str) -> None:
        self._log("ERROR", message)
