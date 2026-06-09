"""
CSV Data Exporter
CSV数据导出模块

Export CSI data and detection results to CSV format for analysis.
"""

import csv
import os
from typing import Dict, List, Optional
from datetime import datetime


class CSVExporter:
    """
    Export CSI data and detection results to CSV files.
    """

    def __init__(self, filepath: str, mode: str = "w"):
        self.filepath = filepath
        self.mode = mode
        self._file = None
        self._writer = None
        self._header_written = False

    def open(self) -> None:
        """Open CSV file for writing"""
        self._file = open(self.filepath, self.mode, newline="")
        self._writer = csv.writer(self._file)

    def close(self) -> None:
        """Close CSV file"""
        if self._file:
            self._file.close()
            self._file = None
            self._writer = None

    def write_header(self, num_subcarriers: int = 64) -> None:
        """Write CSV header"""
        if not self._writer or self._header_written:
            return

        header = ["timestamp", "rssi", "motion_detected", "confidence"]
        header.extend([f"amp_{i}" for i in range(num_subcarriers)])
        self._writer.writerow(header)
        self._header_written = True

    def write_sample(
        self,
        timestamp: float,
        rssi: float,
        motion_detected: bool,
        confidence: float,
        amplitude: List[float]
    ) -> None:
        """Write a single sample row"""
        if not self._writer:
            return

        row = [
            datetime.fromtimestamp(timestamp).isoformat(),
            f"{rssi:.2f}",
            "1" if motion_detected else "0",
            f"{confidence:.4f}"
        ]
        row.extend([f"{a:.6f}" for a in amplitude])
        self._writer.writerow(row)
        self._file.flush()

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
