"""
Terminal Dashboard UI
终端仪表板UI

Real-time TUI dashboard for visualizing CSI data and motion detection results.
使用ASCII图表实时可视化CSI数据和运动检测结果。
"""

import os
import sys
import math
import shutil
import signal
from typing import Dict, List, Optional
from datetime import datetime


class Dashboard:
    """
    Terminal-based real-time dashboard for WaveSense.
    Renders ASCII charts and status information.
    """

    def __init__(self, num_subcarriers: int = 64):
        self.num_subcarriers = num_subcarriers
        self.width = 80
        self.height = 24
        self._running = False
        self._amplitude_history: List[List[float]] = []
        self._max_history = 50
        self._motion_status = "IDLE"
        self._confidence = 0.0
        self._detector_details: Dict = {}
        self._fps = 0.0
        self._sample_count = 0
        self._start_time = 0.0

    def start(self) -> None:
        """Initialize dashboard"""
        self._running = True
        self._start_time = datetime.now().timestamp()
        self._clear_screen()
        self._hide_cursor()

    def stop(self) -> None:
        """Clean up dashboard"""
        self._running = False
        self._show_cursor()
        print("\n")

    def update(
        self,
        amplitude: List[float],
        motion_detected: bool,
        confidence: float,
        detector_details: Dict,
        fps: float = 0.0
    ) -> None:
        """Update dashboard with new data"""
        if not self._running:
            return

        self._sample_count += 1
        self._fps = fps

        # Update amplitude history
        self._amplitude_history.append(amplitude)
        if len(self._amplitude_history) > self._max_history:
            self._amplitude_history.pop(0)

        # Update motion status
        if motion_detected:
            self._motion_status = "MOTION DETECTED"
        else:
            self._motion_status = "NO MOTION"
        self._confidence = confidence
        self._detector_details = detector_details

        # Render
        self._render()

    def _render(self) -> None:
        """Render the dashboard"""
        self._clear_screen()
        lines = []

        # Header
        lines.append(self._color("╔" + "═" * (self.width - 2) + "╗", "cyan"))
        title = " WaveSense-CLI - Wi-Fi CSI Motion Detection "
        lines.append(self._color("║", "cyan") + title.center(self.width - 2) + self._color("║", "cyan"))
        lines.append(self._color("╠" + "═" * (self.width - 2) + "╣", "cyan"))

        # Status bar
        status_color = "red" if self._motion_status == "MOTION DETECTED" else "green"
        status_line = f" Status: {self._color(self._motion_status, status_color)} | Confidence: {self._confidence:.1%} | FPS: {self._fps:.1f} "
        lines.append(self._color("║", "cyan") + status_line.ljust(self.width - 2) + self._color("║", "cyan"))
        lines.append(self._color("╠" + "═" * (self.width - 2) + "╣", "cyan"))

        # Amplitude chart
        lines.append(self._color("║", "cyan") + " Amplitude Spectrum ".ljust(self.width - 2) + self._color("║", "cyan"))
        chart_lines = self._draw_amplitude_chart(8)
        for cl in chart_lines:
            lines.append(self._color("║", "cyan") + cl.ljust(self.width - 2) + self._color("║", "cyan"))

        # Detector details
        lines.append(self._color("╠" + "═" * (self.width - 2) + "╣", "cyan"))
        lines.append(self._color("║", "cyan") + " Detector Details ".ljust(self.width - 2) + self._color("║", "cyan"))

        detail_lines = self._format_detector_details(4)
        for dl in detail_lines:
            lines.append(self._color("║", "cyan") + dl.ljust(self.width - 2) + self._color("║", "cyan"))

        # Footer
        lines.append(self._color("╚" + "═" * (self.width - 2) + "╝", "cyan"))
        lines.append(" Press Ctrl+C to exit ")

        # Output
        output = "\n".join(lines)
        sys.stdout.write(output)
        sys.stdout.flush()

    def _draw_amplitude_chart(self, chart_height: int) -> List[str]:
        """Draw ASCII amplitude chart"""
        if not self._amplitude_history:
            return [" " * (self.width - 2)] * chart_height

        latest = self._amplitude_history[-1]
        if not latest:
            return [" " * (self.width - 2)] * chart_height

        # Normalize to chart height
        max_val = max(latest) if max(latest) > 0 else 1.0
        normalized = [min(chart_height, int(v / max_val * chart_height)) for v in latest]

        # Downsample to fit width
        chart_width = self.width - 4
        if len(normalized) > chart_width:
            step = len(normalized) / chart_width
            normalized = [normalized[int(i * step)] for i in range(chart_width)]
        else:
            normalized = normalized + [0] * (chart_width - len(normalized))

        lines = []
        for row in range(chart_height, 0, -1):
            line = ""
            for val in normalized:
                if val >= row:
                    line += "█"
                elif val >= row - 0.5:
                    line += "▌"
                else:
                    line += " "
            lines.append(line)

        return lines

    def _format_detector_details(self, max_lines: int) -> List[str]:
        """Format detector details for display"""
        lines = []
        for key, value in self._detector_details.items():
            if isinstance(value, float):
                text = f"  {key}: {value:.4f}"
            else:
                text = f"  {key}: {value}"
            lines.append(text[:self.width - 4])
            if len(lines) >= max_lines:
                break
        while len(lines) < max_lines:
            lines.append("")
        return lines

    def _color(self, text: str, color: str) -> str:
        """Apply ANSI color codes"""
        colors = {
            "red": "\033[91m",
            "green": "\033[92m",
            "yellow": "\033[93m",
            "blue": "\033[94m",
            "magenta": "\033[95m",
            "cyan": "\033[96m",
            "white": "\033[97m",
            "reset": "\033[0m"
        }
        code = colors.get(color, colors["reset"])
        reset = colors["reset"]
        return f"{code}{text}{reset}"

    def _clear_screen(self) -> None:
        """Clear terminal screen"""
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    def _hide_cursor(self) -> None:
        """Hide terminal cursor"""
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

    def _show_cursor(self) -> None:
        """Show terminal cursor"""
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()
