"""
WaveSense-CLI - TUI仪表盘 / TUI Dashboard
=============================================

基于终端的实时WiFi信号监控仪表盘。
Terminal-based real-time WiFi signal monitoring dashboard.

使用简单的终端刷新机制（非curses），确保最大兼容性。
Uses simple terminal refresh mechanism (not curses) for maximum compatibility.

功能 / Features:
    - 实时信号列表 / Real-time signal list
    - 最强信号高亮 / Strongest signal highlight
    - 信号统计面板 / Signal statistics panel
    - 异常警报 / Anomaly alerts
    - 键盘交互（q退出, r刷新, s排序）/ Keyboard interaction (q=quit, r=refresh, s=sort)
    - 自动适配终端大小 / Auto-adapt to terminal size
"""

from __future__ import annotations

import logging
import os
import select
import sys
import termios
import time
import tty
from typing import Callable, Dict, List, Optional

from .analyzer import calculate_statistics, detect_anomalies, get_signal_summary
from .config import get_config
from .models import AnalysisResult, ScanResult, SignalHistory, SignalRecord, WiFiSignal
from .scanner import WiFiScanner
from .utils import (
    Colors,
    clear_screen,
    colorize,
    format_timestamp,
    get_terminal_size,
    hide_cursor,
    rssi_to_percentage,
    show_cursor,
    signal_color,
)
from .visualizer import (
    BOX_BL,
    BOX_BR,
    BOX_B,
    BOX_H,
    BOX_L,
    BOX_R,
    BOX_T,
    BOX_TL,
    BOX_TR,
    BOX_V,
    BOX_X,
    PROGRESS_EMPTY,
    PROGRESS_FULL,
    render_signal_bar,
)

logger = logging.getLogger("wavesense.dashboard")


# ============================================================
# 仪表盘状态 / Dashboard State
# ============================================================
class DashboardState:
    """仪表盘状态管理 / Dashboard state management"""

    def __init__(self) -> None:
        self.sort_by: str = "rssi"       # 排序字段 / Sort field: rssi, ssid, channel
        self.sort_reverse: bool = True   # 降序 / Descending
        self.filter_level: str = ""      # 信号等级过滤 / Signal level filter
        self.show_details: bool = False  # 显示详细信息 / Show details
        self.selected_index: int = 0     # 选中行 / Selected row
        self.scan_count: int = 0         # 扫描计数 / Scan count
        self.anomaly_count: int = 0      # 异常计数 / Anomaly count
        self.last_error: str = ""        # 最后错误 / Last error


# ============================================================
# TUI仪表盘 / TUI Dashboard
# ============================================================
class Dashboard:
    """
    TUI仪表盘 / TUI Dashboard
    ==========================
    实时WiFi信号监控终端仪表盘。
    Real-time WiFi signal monitoring terminal dashboard.

    Usage / 用法:
        dashboard = Dashboard()
        dashboard.run()

    键盘控制 / Keyboard Controls:
        q / ESC  - 退出 / Quit
        r       - 手动刷新 / Manual refresh
        s       - 切换排序方式 / Toggle sort method
        d       - 切换详细模式 / Toggle detail mode
        UP/DOWN - 选择信号 / Select signal
        1-5     - 按信号等级过滤 / Filter by signal level
        0       - 清除过滤 / Clear filter
    """

    def __init__(
        self,
        scanner: Optional[WiFiScanner] = None,
        refresh_interval: Optional[float] = None,
    ) -> None:
        """
        初始化仪表盘 / Initialize dashboard

        Args / 参数:
            scanner: WiFi扫描器实例 / WiFi scanner instance
            refresh_interval: 刷新间隔（秒）/ Refresh interval in seconds
        """
        self._scanner = scanner or WiFiScanner()
        config = get_config()
        self._refresh_interval = refresh_interval or config.get("dashboard", "refresh_interval", 2.0)
        self._max_display = config.get("dashboard", "max_display", 20)
        self._state = DashboardState()
        self._current_result: Optional[ScanResult] = None
        self._history = SignalHistory()
        self._running = False
        self._last_refresh = 0.0

    @property
    def state(self) -> DashboardState:
        """当前状态 / Current state"""
        return self._state

    def run(self) -> None:
        """
        启动仪表盘 / Start dashboard
        ==============================
        进入主循环，实时显示WiFi信号信息。
        Enter main loop, display WiFi signal info in real-time.
        """
        self._running = True
        self._state.last_error = ""

        # 隐藏光标 / Hide cursor
        hide_cursor()

        try:
            while self._running:
                # 检查键盘输入 / Check keyboard input
                self._check_input()

                # 定时刷新数据 / Refresh data periodically
                now = time.time()
                if now - self._last_refresh >= self._refresh_interval:
                    self._refresh_data()
                    self._last_refresh = now

                # 渲染界面 / Render interface
                self._render()

                # 短暂休眠 / Brief sleep
                time.sleep(0.1)

        except KeyboardInterrupt:
            pass
        finally:
            # 恢复光标 / Restore cursor
            show_cursor()
            clear_screen()
            print(colorize("  WaveSense-CLI 仪表盘已退出 / Dashboard exited.", Colors.DIM))

    def _check_input(self) -> None:
        """
        检查键盘输入（非阻塞）/ Check keyboard input (non-blocking)
        ==============================================================
        使用select实现非阻塞输入检测，兼容Linux/macOS。
        Use select for non-blocking input detection, compatible with Linux/macOS.
        """
        try:
            # 检查stdin是否有数据可读 / Check if stdin has data to read
            if sys.stdin.isatty():
                # Linux/macOS: 使用select / Linux/macOS: use select
                if hasattr(select, "select"):
                    dr, _, _ = select.select([sys.stdin], [], [], 0.0)
                    if dr:
                        key = sys.stdin.read(1)
                        self._handle_key(key)
                else:
                    # Windows回退 / Windows fallback - 不支持非阻塞读取
                    pass
        except (IOError, OSError):
            pass

    def _handle_key(self, key: str) -> None:
        """
        处理键盘输入 / Handle keyboard input

        Args / 参数:
            key: 按键字符 / Key character
        """
        key_lower = key.lower()

        if key_lower in ("q", "\x1b"):  # q 或 ESC
            self._running = False
        elif key_lower == "r":
            self._refresh_data()
        elif key_lower == "s":
            self._toggle_sort()
        elif key_lower == "d":
            self._state.show_details = not self._state.show_details
        elif key_lower == "0":
            self._state.filter_level = ""
        elif key_lower in ("1", "2", "3", "4", "5"):
            levels = ["excellent", "strong", "good", "weak", "very_weak"]
            idx = int(key_lower) - 1
            if idx < len(levels):
                self._state.filter_level = levels[idx]
        elif key == "\x1b[A":  # UP arrow
            self._state.selected_index = max(0, self._state.selected_index - 1)
        elif key == "\x1b[B":  # DOWN arrow
            self._state.selected_index = min(
                self._max_display - 1, self._state.selected_index + 1
            )

    def _toggle_sort(self) -> None:
        """切换排序方式 / Toggle sort method"""
        sort_options = ["rssi", "ssid", "channel", "frequency"]
        current_idx = sort_options.index(self._state.sort_by) if self._state.sort_by in sort_options else 0
        next_idx = (current_idx + 1) % len(sort_options)
        self._state.sort_by = sort_options[next_idx]
        self._state.sort_reverse = not self._state.sort_reverse if next_idx == 0 else True

    def _refresh_data(self) -> None:
        """刷新扫描数据 / Refresh scan data"""
        try:
            result = self._scanner.scan(use_cache=False)
            self._current_result = result
            self._state.scan_count += 1
            self._state.last_error = result.error or ""

            # 更新历史 / Update history
            for signal in result.signals:
                self._history.add_record(SignalRecord(
                    ssid=signal.ssid,
                    bssid=signal.bssid,
                    rssi=signal.rssi,
                    timestamp=signal.timestamp,
                ))

            # 检测异常 / Detect anomalies
            if self._history.record_count >= 5:
                anomalies = detect_anomalies(self._history)
                self._state.anomaly_count = len(anomalies)

        except Exception as e:
            self._state.last_error = f"扫描错误: {e} / Scan error: {e}"
            logger.error("仪表盘刷新失败: %s / Dashboard refresh failed: %s", e)

    def _render(self) -> None:
        """渲染仪表盘界面 / Render dashboard interface"""
        term_w, term_h = get_terminal_size()
        clear_screen()

        lines: List[str] = []
        y = 0  # 当前行号 / Current line number

        # === 标题栏 / Title Bar ===
        title = colorize(
            f"  WaveSense-CLI 信号仪表盘 / Signal Dashboard",
            Colors.BOLD + Colors.BRIGHT_CYAN,
        )
        status_right = (
            f"扫描: {self._state.scan_count} | "
            f"异常: {self._state.anomaly_count} | "
            f"排序: {self._state.sort_by} | "
            f"刷新: {self._refresh_interval}s"
        )
        # 右对齐状态 / Right-align status
        padding = max(0, term_w - len(title) - len(status_right) - 4)
        header = f"{title}{' ' * padding}{colorize(status_right, Colors.DIM)}"
        lines.append(header)
        lines.append(colorize(f"  {'─' * (term_w - 4)}", Colors.DIM))
        y += 2

        # === 错误信息 / Error Info ===
        if self._state.last_error:
            lines.append(colorize(f"  ⚠ {self._state.last_error}", Colors.BRIGHT_RED))
            y += 1

        # === 统计面板 / Statistics Panel ===
        if self._current_result and self._current_result.signals:
            stats = calculate_statistics(self._current_result.signals)
            stats_lines = self._render_stats_panel(stats, term_w)
            lines.extend(stats_lines)
            y += len(stats_lines)

        # === 最强信号 / Strongest Signal ===
        if self._current_result and self._current_result.strongest_signal:
            s = self._current_result.strongest_signal
            lines.append("")
            lines.append(
                f"  {colorize('★ 最强信号 / Strongest:', Colors.BRIGHT_YELLOW)} "
                f"{s.ssid or '(隐藏/Hidden)'} "
                f"{colorize(f'{s.rssi} dBm', signal_color(s.rssi))} "
                f"Ch:{s.channel}"
            )
            y += 2

        # === 信号列表 / Signal List ===
        if self._current_result:
            signal_lines = self._render_signal_list(self._current_result.signals, term_w, term_h - y - 5)
            lines.extend(signal_lines)

        # === 底部帮助栏 / Bottom Help Bar ===
        lines.append("")
        help_text = colorize(
            "  [q]退出/Quit  [r]刷新/Refresh  [s]排序/Sort  [d]详情/Detail  [1-5]过滤/Filter  [0]清除/Clear",
            Colors.DIM,
        )
        lines.append(help_text)

        # 输出所有行 / Output all lines
        output = "\n".join(lines)
        sys.stdout.write(output)
        sys.stdout.flush()

    def _render_stats_panel(self, stats, term_w: int) -> List[str]:
        """
        渲染统计面板 / Render statistics panel

        Args / 参数:
            stats: 统计数据 / Statistics data
            term_w: 终端宽度 / Terminal width

        Returns / 返回:
            面板行列表 / List of panel lines
        """
        lines: List[str] = []
        lines.append("")
        lines.append(
            f"  {colorize('📊 统计 / Statistics:', Colors.BRIGHT_CYAN)} "
            f"信号数/Count: {stats.count} | "
            f"均值/Mean: {stats.mean:.1f} | "
            f"中位/Median: {stats.median:.1f} | "
            f"标准差/Std: {stats.std_dev:.1f} | "
            f"范围/Range: {stats.min_val:.0f}~{stats.max_val:.0f} dBm"
        )
        return lines

    def _render_signal_list(
        self, signals: List[WiFiSignal], term_w: int, max_lines: int
    ) -> List[str]:
        """
        渲染信号列表 / Render signal list

        Args / 参数:
            signals: WiFi信号列表 / List of WiFi signals
            term_w: 终端宽度 / Terminal width
            max_lines: 最大行数 / Maximum lines

        Returns / 返回:
            列表行 / List lines
        """
        lines: List[str] = []

        if not signals:
            lines.append(f"  {colorize('  (无信号 / No signals detected)', Colors.DIM)}")
            return lines

        # 过滤 / Filter
        filtered = signals
        if self._state.filter_level:
            filtered = [s for s in signals if s.signal_level.value == self._state.filter_level]

        # 排序 / Sort
        sort_key = self._state.sort_by
        reverse = self._state.sort_reverse
        if sort_key == "rssi":
            sorted_signals = sorted(filtered, key=lambda s: s.rssi, reverse=reverse)
        elif sort_key == "ssid":
            sorted_signals = sorted(filtered, key=lambda s: s.ssid.lower(), reverse=not reverse)
        elif sort_key == "channel":
            sorted_signals = sorted(filtered, key=lambda s: s.channel, reverse=reverse)
        else:
            sorted_signals = sorted(filtered, key=lambda s: s.rssi, reverse=True)

        # 表头 / Header
        lines.append("")
        header = (
            f"  {'#':>3}  {'SSID':<24} {'BSSID':<17} "
            f"{'RSSI':>5} {'%':>4} {'Ch':>4} {'等级/Level':<12}"
        )
        lines.append(colorize(header, Colors.BOLD))
        lines.append(colorize(f"  {'─' * 3}  {'─' * 24} {'─' * 17} {'─' * 5} {'─' * 4} {'─' * 4} {'─' * 12}", Colors.DIM))

        # 信号行 / Signal rows
        display_count = min(len(sorted_signals), max_lines, self._max_display)
        for i in range(display_count):
            if i >= len(sorted_signals):
                break

            signal = sorted_signals[i]
            ssid = signal.ssid or "(隐藏/Hidden)"
            if len(ssid) > 24:
                ssid = ssid[:22] + ".."

            # 选中高亮 / Selection highlight
            marker = colorize(">", Colors.BRIGHT_YELLOW) if i == self._state.selected_index else " "

            rssi_str = colorize(f"{signal.rssi:>4}", signal_color(signal.rssi))
            pct = rssi_to_percentage(signal.rssi)
            level = signal.signal_level.value

            row = (
                f"  {marker}{i + 1:>2}  {ssid:<24} {signal.bssid:<17} "
                f"{rssi_str} {pct:>3}% {signal.channel:>4} {level:<12}"
            )

            # 详细模式 / Detail mode
            if self._state.show_details:
                freq_str = f"{signal.frequency} MHz" if signal.frequency > 0 else "N/A"
                sec = signal.security if signal.security else "Open"
                row += f" | {freq_str} | {sec}"

            lines.append(row)

        if len(sorted_signals) > display_count:
            lines.append(
                colorize(f"  ... 还有 {len(sorted_signals) - display_count} 个信号 / ... {len(sorted_signals) - display_count} more", Colors.DIM)
            )

        return lines


# ============================================================
# 简单仪表盘模式（不依赖select）/ Simple Dashboard Mode (no select dependency)
# ============================================================
def run_simple_dashboard(
    scanner: Optional[WiFiScanner] = None,
    interval: float = 5.0,
    max_scans: Optional[int] = None,
) -> None:
    """
    运行简单仪表盘模式 / Run simple dashboard mode
    ==================================================
    不依赖select/termios的简单刷新模式，最大兼容性。
    Simple refresh mode without select/termios dependency, maximum compatibility.

    Args / 参数:
        scanner: WiFi扫描器 / WiFi scanner
        interval: 刷新间隔 / Refresh interval
        max_scans: 最大扫描次数 / Maximum scans
    """
    from .visualizer import render_dashboard_summary, render_signal_bars

    scanner = scanner or WiFiScanner()
    history = SignalHistory()
    scan_count = 0

    print(colorize("\n  WaveSense-CLI 简易仪表盘 / Simple Dashboard", Colors.BOLD + Colors.BRIGHT_CYAN))
    print(colorize(f"  按 Ctrl+C 退出 / Press Ctrl+C to quit\n", Colors.DIM))

    try:
        while max_scans is None or scan_count < max_scans:
            clear_screen()

            # 扫描 / Scan
            result = scanner.scan(use_cache=False)
            scan_count += 1

            # 更新历史 / Update history
            for signal in result.signals:
                history.add_record(SignalRecord(
                    ssid=signal.ssid,
                    bssid=signal.bssid,
                    rssi=signal.rssi,
                    timestamp=signal.timestamp,
                ))

            # 分析 / Analyze
            from .analyzer import analyze_scan_result
            analysis = analyze_scan_result(result) if result.signals else None

            # 异常检测 / Anomaly detection
            if history.record_count >= 5:
                anomalies = detect_anomalies(history)
                if anomalies:
                    analysis = analysis or analyze_scan_result(result)
                    analysis.anomalies = anomalies

            # 渲染 / Render
            print(render_dashboard_summary(result, analysis))
            print()
            print(render_signal_bars(result.signals, width=40))

            # 下次刷新提示 / Next refresh hint
            print()
            print(colorize(
                f"  [扫描 #{scan_count}] 下次刷新 / Next refresh in {interval:.0f}s... (Ctrl+C 退出/quit)",
                Colors.DIM,
            ))

            time.sleep(interval)

    except KeyboardInterrupt:
        clear_screen()
        print(colorize(f"\n  仪表盘已退出（共 {scan_count} 次扫描）/ Dashboard exited ({scan_count} scans total).", Colors.DIM))
