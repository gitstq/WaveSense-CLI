"""
WaveSense-CLI - ASCII可视化引擎 / ASCII Visualization Engine
==============================================================

使用Unicode字符和ANSI颜色在终端中渲染信号可视化图表。
Renders signal visualization charts in terminal using Unicode characters and ANSI colors.

包含 / Contains:
    - ASCII热力图 / ASCII heatmap
    - 信号强度条形图 / Signal strength bar chart
    - 信号历史趋势折线图 / Signal history trend line chart
    - 仪表盘摘要面板 / Dashboard summary panel

使用Unicode方块字符: ▁▂▃▄▅▆▇█
Uses Unicode block characters: ▁▂▃▄▅▆▇█
"""

from __future__ import annotations

import math
import os
import sys
from typing import Dict, List, Optional, Tuple

from .models import (
    AnalysisResult,
    ScanResult,
    SignalHistory,
    SignalStatistics,
    WiFiSignal,
    classify_signal,
)
from .utils import (
    Colors,
    colorize,
    format_timestamp,
    get_terminal_size,
    rssi_to_percentage,
    signal_color,
)

# ============================================================
# Unicode绘图字符 / Unicode Drawing Characters
# ============================================================
# 方块字符（从低到高）/ Block characters (low to high)
BLOCK_CHARS = [" ", "▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]

# 进度条字符 / Progress bar characters
PROGRESS_FULL = "█"
PROGRESS_EMPTY = "░"

# 边框字符 / Border characters
BOX_TL = "┌"    # 左上 / Top-left
BOX_TR = "┐"    # 右上 / Top-right
BOX_BL = "└"    # 左下 / Bottom-left
BOX_BR = "┘"    # 右下 / Bottom-right
BOX_H = "─"     # 水平 / Horizontal
BOX_V = "│"     # 垂直 / Vertical
BOX_L = "├"     # 左T / Left-T
BOX_R = "┤"     # 右T / Right-T
BOX_T = "┬"     # 上T / Top-T
BOX_B = "┴"     # 下T / Bottom-T
BOX_X = "┼"     # 十字 / Cross

# 折线图点字符 / Line chart point characters
POINT_CHARS = ["·", "○", "●", "◆"]

# 热力图颜色等级（ANSI）/ Heatmap color levels (ANSI)
HEATMAP_COLORS = [
    Colors.BG_BLUE,       # 极弱 / Very weak
    Colors.BG_CYAN,       # 弱 / Weak
    Colors.BG_GREEN,       # 中 / Good
    Colors.BG_YELLOW,      # 强 / Strong
    Colors.BG_RED,        # 极强 / Excellent
]


# ============================================================
# 信号强度条形图 / Signal Strength Bar Chart
# ============================================================
def render_signal_bar(rssi: int, width: int = 20, show_label: bool = True) -> str:
    """
    渲染信号强度条形图 / Render signal strength bar chart
    =======================================================
    使用方块字符显示信号强度百分比。

    Args / 参数:
        rssi: 信号强度（dBm）/ Signal strength in dBm
        width: 条形图宽度 / Bar chart width
        show_label: 是否显示标签 / Whether to show label

    Returns / 返回:
        格式化的条形图字符串 / Formatted bar chart string
    """
    percentage = rssi_to_percentage(rssi)
    filled = int(width * percentage / 100)

    # 根据信号强度选择颜色 / Choose color based on signal strength
    color = signal_color(rssi)

    bar = colorize(PROGRESS_FULL * filled, color)
    bar += colorize(PROGRESS_EMPTY * (width - filled), Colors.DIM)

    if show_label:
        label = f"{rssi} dBm ({percentage}%)"
        return f"[{bar}] {label}"
    return f"[{bar}]"


def render_signal_bars(signals: List[WiFiSignal], width: int = 30) -> str:
    """
    渲染多个信号的条形图列表 / Render bar chart list for multiple signals

    Args / 参数:
        signals: WiFi信号列表 / List of WiFi signals
        width: 条形图宽度 / Bar chart width

    Returns / 返回:
        格式化的多信号条形图 / Formatted multi-signal bar chart
    """
    if not signals:
        return "  (无信号数据 / No signal data)"

    # 按信号强度排序 / Sort by signal strength
    sorted_signals = sorted(signals, key=lambda s: s.rssi, reverse=True)

    lines: List[str] = []
    lines.append(f"  {'SSID':<24} {'RSSI':>6}  {'信号强度 / Signal Strength'}")
    lines.append(f"  {'─' * 24} {'─' * 6}  {'─' * (width + 2)}")

    for signal in sorted_signals[:15]:  # 最多显示15个 / Show max 15
        ssid = (signal.ssid[:22] + "..") if len(signal.ssid) > 24 else signal.ssid
        if not signal.ssid:
            ssid = "(隐藏/Hidden)"
        bar = render_signal_bar(signal.rssi, width=width, show_label=False)
        lines.append(f"  {ssid:<24} {signal.rssi:>4}dBm  {bar}")

    return "\n".join(lines)


# ============================================================
# ASCII热力图 / ASCII Heatmap
# ============================================================
def render_heatmap(
    data: List[List[float]],
    width: Optional[int] = None,
    height: Optional[int] = None,
    title: str = "信号热力图 / Signal Heatmap",
    x_labels: Optional[List[str]] = None,
    y_labels: Optional[List[str]] = None,
    use_color: bool = True,
) -> str:
    """
    渲染ASCII热力图 / Render ASCII heatmap
    ========================================
    使用Unicode方块字符和ANSI颜色渲染二维数据热力图。
    Render 2D data heatmap using Unicode block characters and ANSI colors.

    Args / 参数:
        data: 二维数据矩阵（值范围0-1）/ 2D data matrix (values 0-1)
        width: 输出宽度（字符）/ Output width in characters
        height: 输出高度（行）/ Output height in rows
        title: 图表标题 / Chart title
        x_labels: X轴标签 / X-axis labels
        y_labels: Y轴标签 / Y-axis labels
        use_color: 是否使用颜色 / Whether to use colors

    Returns / 返回:
        热力图字符串 / Heatmap string
    """
    if not data or not data[0]:
        return f"  (无数据 / No data)"

    rows = len(data)
    cols = len(data[0])

    # 确定输出尺寸 / Determine output size
    term_w, _ = get_terminal_size()
    if width is None:
        width = min(term_w - 10, cols * 2)
    if height is None:
        height = min(rows, 20)

    lines: List[str] = []

    # 标题 / Title
    if title:
        lines.append(f"  {colorize(title, Colors.BOLD)}")
        lines.append("")

    # Y轴标签最大宽度 / Max Y-axis label width
    y_label_width = max((len(str(l)) for l in y_labels), default=0) if y_labels else 0

    # 渲染热力图行 / Render heatmap rows
    for row_idx in range(height):
        # 数据行索引映射 / Data row index mapping
        data_row = int(row_idx * rows / height)

        # Y轴标签 / Y-axis label
        y_label = ""
        if y_labels and data_row < len(y_labels):
            y_label = f"{y_labels[data_row]:>{y_label_width}} "

        row_data = data[data_row]
        row_str = y_label

        for col_idx in range(width):
            # 数据列索引映射 / Data column index mapping
            data_col = int(col_idx * cols / width)

            if data_col < len(row_data):
                value = max(0.0, min(1.0, row_data[data_col]))
                # 选择方块字符 / Choose block character
                char_idx = min(int(value * (len(BLOCK_CHARS) - 1)), len(BLOCK_CHARS) - 1)
                char = BLOCK_CHARS[char_idx]

                # 应用颜色 / Apply color
                if use_color and sys.stdout.isatty():
                    color_idx = min(int(value * (len(HEATMAP_COLORS) - 1)), len(HEATMAP_COLORS) - 1)
                    row_str += f"{HEATMAP_COLORS[color_idx]}{char}{Colors.RESET}"
                else:
                    row_str += char
            else:
                row_str += " "

        lines.append(f"  {row_str}")

    # X轴标签 / X-axis labels
    if x_labels:
        lines.append("")
        x_label_line = " " * (y_label_width + 2)
        step = max(1, width // len(x_labels))
        for i, label in enumerate(x_labels):
            pos = int(i * width / len(x_labels))
            x_label_line = x_label_line[:pos + y_label_width + 2] + label[:3] + x_label_line[pos + y_label_width + 5:]
        lines.append(f"  {x_label_line}")

    # 图例 / Legend
    lines.append("")
    legend = "  图例/Legend: "
    labels_legend = ["弱/Weak", "中/Medium", "强/Strong"]
    for i, label in enumerate(labels_legend):
        if use_color and sys.stdout.isatty():
            legend += f"{HEATMAP_COLORS[i * 2]}{BLOCK_CHARS[i * 2 + 4]}{Colors.RESET} {label}  "
        else:
            legend += f"{BLOCK_CHARS[i * 2 + 4]} {label}  "
    lines.append(legend)

    return "\n".join(lines)


def render_channel_heatmap(signals: List[WiFiSignal]) -> str:
    """
    渲染WiFi信道使用热力图 / Render WiFi channel usage heatmap
    =============================================================
    将WiFi信道使用情况可视化为热力图。
    Visualize WiFi channel usage as a heatmap.

    Args / 参数:
        signals: WiFi信号列表 / List of WiFi signals

    Returns / 返回:
        信道热力图字符串 / Channel heatmap string
    """
    if not signals:
        return "  (无信号数据 / No signal data)"

    # 统计信道使用 / Count channel usage
    channel_counts: Dict[int, int] = {}
    for s in signals:
        if s.channel > 0:
            channel_counts[s.channel] = channel_counts.get(s.channel, 0) + 1

    if not channel_counts:
        return "  (无信道数据 / No channel data)"

    max_count = max(channel_counts.values())
    if max_count == 0:
        max_count = 1

    # 构建2.4GHz信道热力图 / Build 2.4GHz channel heatmap (channels 1-14)
    channels_24 = list(range(1, 15))
    data_24 = []
    for ch in channels_24:
        count = channel_counts.get(ch, 0)
        data_24.append(count / max_count)

    lines: List[str] = []
    lines.append(f"  {colorize('2.4GHz 信道使用热力图 / 2.4GHz Channel Usage Heatmap', Colors.BOLD)}")
    lines.append("")

    # 信道标签 / Channel labels
    header = "    "
    for ch in channels_24:
        header += f"{ch:>3}"
    lines.append(header)

    # 热力图行 / Heatmap row
    row = "    "
    for value in data_24:
        char_idx = min(int(value * (len(BLOCK_CHARS) - 1)), len(BLOCK_CHARS) - 1)
        char = BLOCK_CHARS[char_idx]
        count = int(value * max_count)

        if sys.stdout.isatty() and value > 0:
            color_idx = min(int(value * (len(HEATMAP_COLORS) - 1)), len(HEATMAP_COLORS) - 1)
            row += f"{HEATMAP_COLORS[color_idx]}{char:>2}{Colors.RESET}"
        else:
            row += f"{char:>2}"
    lines.append(row)

    # 数值行 / Value row
    val_row = "    "
    for ch in channels_24:
        count = channel_counts.get(ch, 0)
        val_row += f"{count:>3}"
    lines.append(val_row)

    # 5GHz信道（如果有）/ 5GHz channels (if any)
    channels_5 = sorted([ch for ch in channel_counts if ch >= 36])
    if channels_5:
        lines.append("")
        lines.append(f"  {colorize('5GHz 信道使用 / 5GHz Channel Usage', Colors.BOLD)}")
        for ch in channels_5:
            count = channel_counts[ch]
            bar_width = int(20 * count / max_count)
            bar = PROGRESS_FULL * bar_width + PROGRESS_EMPTY * (20 - bar_width)
            lines.append(f"    Ch {ch:>3}: [{bar}] {count} APs")

    return "\n".join(lines)


# ============================================================
# ASCII折线图 / ASCII Line Chart
# ============================================================
def render_signal_chart(
    history: SignalHistory,
    bssid: Optional[str] = None,
    width: int = 60,
    height: int = 15,
    title: Optional[str] = None,
) -> str:
    """
    渲染信号历史趋势ASCII折线图 / Render signal history trend ASCII line chart
    ==============================================================================
    使用Unicode字符绘制信号强度随时间变化的折线图。
    Draw a line chart of signal strength over time using Unicode characters.

    Args / 参数:
        history: 信号历史记录 / Signal history records
        bssid: 指定BSSID（可选）/ Specific BSSID (optional)
        width: 图表宽度 / Chart width
        height: 图表高度 / Chart height
        title: 图表标题 / Chart title

    Returns / 返回:
        折线图字符串 / Line chart string
    """
    if history.record_count == 0:
        return "  (无历史数据 / No history data)"

    # 获取数据 / Get data
    if bssid:
        records = history.get_by_bssid(bssid)
        ssid = records[0].ssid if records else bssid
    else:
        # 使用所有信号的平均值 / Use average of all signals
        # 按时间分组 / Group by time
        time_groups: Dict[float, List[int]] = {}
        for r in history.records:
            # 四舍五入到秒 / Round to nearest second
            t = round(r.timestamp)
            if t not in time_groups:
                time_groups[t] = []
            time_groups[t].append(r.rssi)

        records = [
            type("Record", (), {"rssi": int(sum(v) / len(v)), "timestamp": t, "ssid": "平均/Average", "bssid": ""})()
            for t, v in sorted(time_groups.items())
        ]
        ssid = "所有信号平均 / All Signals Average"

    if not records:
        return "  (无匹配数据 / No matching data)"

    rssi_values = [r.rssi for r in records]
    min_rssi = min(rssi_values)
    max_rssi = max(rssi_values)

    # 扩展范围使图表更美观 / Expand range for better visualization
    rssi_range = max_rssi - min_rssi
    if rssi_range < 10:
        mid = (max_rssi + min_rssi) / 2
        min_rssi = mid - 5
        max_rssi = mid + 5
        rssi_range = 10

    lines: List[str] = []

    # 标题 / Title
    chart_title = title or f"信号趋势 / Signal Trend: {ssid}"
    lines.append(f"  {colorize(chart_title, Colors.BOLD)}")
    lines.append(f"  数据点: {len(records)} | 范围: {min_rssi:.0f} ~ {max_rssi:.0f} dBm")
    lines.append("")

    # Y轴标签 / Y-axis labels
    y_label_width = 6

    # 构建图表网格 / Build chart grid
    chart: List[List[str]] = [[" " for _ in range(width)] for _ in range(height)]

    # 绘制数据点 / Plot data points
    point_positions: List[Tuple[int, int]] = []
    for i, record in enumerate(records):
        x = int(i * (width - 1) / max(len(records) - 1, 1))
        y = height - 1 - int((record.rssi - min_rssi) / rssi_range * (height - 1))
        y = max(0, min(height - 1, y))
        chart[y][x] = "●"
        point_positions.append((x, y))

    # 绘制连线 / Draw connecting lines
    for i in range(len(point_positions) - 1):
        x1, y1 = point_positions[i]
        x2, y2 = point_positions[i + 1]

        # 简单的线性插值 / Simple linear interpolation
        steps = max(abs(x2 - x1), abs(y2 - y1), 1)
        for step in range(1, steps):
            t = step / steps
            x = int(x1 + t * (x2 - x1))
            y = int(y1 + t * (y2 - y1))
            if 0 <= x < width and 0 <= y < height:
                if chart[y][x] == " ":
                    # 选择合适的连线字符 / Choose appropriate line character
                    if y2 > y1:
                        chart[y][x] = "╱"
                    elif y2 < y1:
                        chart[y][x] = "╲"
                    else:
                        chart[y][x] = "─"

    # 渲染图表 / Render chart
    for row in range(height):
        rssi_val = max_rssi - (row * rssi_range / (height - 1))
        y_label = f"{rssi_val:>5.0f} "

        chart_line = y_label + BOX_V
        for col in range(width):
            char = chart[row][col]
            if char == "●":
                chart_line += colorize(char, Colors.BRIGHT_CYAN)
            elif char in ("╱", "╲"):
                chart_line += colorize(char, Colors.CYAN)
            elif char == "─":
                chart_line += colorize(char, Colors.CYAN)
            else:
                chart_line += char
        chart_line += BOX_V
        lines.append(f"  {chart_line}")

    # X轴 / X-axis
    x_axis = " " * y_label_width + BOX_BL + BOX_H * width + BOX_BR
    lines.append(f"  {x_axis}")

    # 时间标签 / Time labels
    if len(records) >= 2:
        first_time = format_timestamp(records[0].timestamp, "%H:%M:%S")
        last_time = format_timestamp(records[-1].timestamp, "%H:%M:%S")
        time_label = " " * (y_label_width + 1) + first_time
        time_label += " " * (width - len(first_time) - len(last_time) - 2)
        time_label += last_time
        lines.append(f"  {time_label}")

    return "\n".join(lines)


# ============================================================
# 仪表盘摘要面板 / Dashboard Summary Panel
# ============================================================
def render_dashboard_summary(
    result: ScanResult,
    analysis: Optional[AnalysisResult] = None,
    width: int = 70,
) -> str:
    """
    渲染仪表盘摘要面板 / Render dashboard summary panel
    =====================================================
    综合显示扫描结果和分析数据的摘要面板。
    Summary panel displaying scan results and analysis data comprehensively.

    Args / 参数:
        result: 扫描结果 / Scan result
        analysis: 分析结果（可选）/ Analysis result (optional)
        width: 面板宽度 / Panel width

    Returns / 返回:
        摘要面板字符串 / Summary panel string
    """
    lines: List[str] = []

    # 顶部边框 / Top border
    lines.append(f"  {BOX_TL}{BOX_H * width}{BOX_TR}")

    # 标题 / Title
    title = "WaveSense-CLI 信号感知面板 / Signal Intelligence Panel"
    title_padding = width - len(title)
    if title_padding > 0:
        title = " " * (title_padding // 2) + title + " " * (title_padding - title_padding // 2)
    lines.append(f"  {BOX_V}{colorize(title, Colors.BOLD + Colors.BRIGHT_CYAN)}{BOX_V}")

    # 分隔线 / Separator
    lines.append(f"  {BOX_L}{BOX_T * width}{BOX_R}")

    # 扫描信息 / Scan info
    scan_time = format_timestamp(result.scan_time, "%Y-%m-%d %H:%M:%S")
    lines.append(f"  {BOX_V} 扫描时间 / Scan Time: {scan_time}")
    lines.append(f"  {BOX_V} 发现信号 / Signals Found: {colorize(str(result.signal_count), Colors.BRIGHT_GREEN)}")
    lines.append(f"  {BOX_V} 平台 / Platform: {result.platform or 'N/A'}")
    if result.scan_duration > 0:
        lines.append(f"  {BOX_V} 耗时 / Duration: {result.scan_duration:.2f}s")

    lines.append(f"  {BOX_V}{BOX_T * width}{BOX_R}")

    # 最强信号 / Strongest signal
    if result.strongest_signal:
        s = result.strongest_signal
        lines.append(f"  {BOX_V} {colorize('★ 最强信号 / Strongest Signal', Colors.BRIGHT_YELLOW)}")
        lines.append(f"  {BOX_V}   SSID: {s.ssid or '(隐藏/Hidden)'}")
        lines.append(f"  {BOX_V}   BSSID: {s.bssid}")
        lines.append(f"  {BOX_V}   RSSI: {colorize(f'{s.rssi} dBm', signal_color(s.rssi))} [{s.signal_level.value}]")
        lines.append(f"  {BOX_V}{BOX_T * width}{BOX_R}")

    # 信号统计 / Signal statistics
    if analysis and analysis.statistics:
        stats = analysis.statistics
        lines.append(f"  {BOX_V} {colorize('📊 信号统计 / Signal Statistics', Colors.BRIGHT_CYAN)}")
        lines.append(f"  {BOX_V}   平均 / Mean:   {stats.mean:.1f} dBm")
        lines.append(f"  {BOX_V}   中位 / Median: {stats.median:.1f} dBm")
        lines.append(f"  {BOX_V}   标准差 / Std:   {stats.std_dev:.1f} dBm")
        lines.append(f"  {BOX_V}   范围 / Range:   {stats.min_val:.0f} ~ {stats.max_val:.0f} dBm")
        lines.append(f"  {BOX_V}{BOX_T * width}{BOX_R}")

    # 异常警报 / Anomaly alerts
    if analysis and analysis.anomalies:
        lines.append(f"  {BOX_V} {colorize(f'⚠ 异常警报 / Anomaly Alerts: {len(analysis.anomalies)}', Colors.BRIGHT_RED)}")
        for anomaly in analysis.anomalies[:3]:
            lines.append(f"  {BOX_V}   ! {anomaly.ssid or anomaly.bssid}: {anomaly.description}")
        if len(analysis.anomalies) > 3:
            lines.append(f"  {BOX_V}   ... 还有 {len(analysis.anomalies) - 3} 个异常 / ... {len(analysis.anomalies) - 3} more")
        lines.append(f"  {BOX_V}{BOX_T * width}{BOX_R}")

    # 信号列表 / Signal list
    if result.signals:
        lines.append(f"  {BOX_V} {colorize('📡 信号列表 / Signal List', Colors.BRIGHT_GREEN)}")
        sorted_signals = sorted(result.signals, key=lambda s: s.rssi, reverse=True)
        for signal in sorted_signals[:10]:
            ssid = (signal.ssid[:20] + "..") if len(signal.ssid) > 22 else (signal.ssid or "(隐藏/Hidden)")
            rssi_str = colorize(f"{signal.rssi:>4}", signal_color(signal.rssi))
            lines.append(f"  {BOX_V}   {ssid:<24} {rssi_str} dBm  Ch:{signal.channel:>3}")
        if len(sorted_signals) > 10:
            lines.append(f"  {BOX_V}   ... 还有 {len(sorted_signals) - 10} 个信号 / ... {len(sorted_signals) - 10} more signals")

    # 底部边框 / Bottom border
    lines.append(f"  {BOX_BL}{BOX_H * width}{BOX_BR}")

    return "\n".join(lines)


# ============================================================
# 信号强度分布图 / Signal Strength Distribution
# ============================================================
def render_distribution(signals: List[WiFiSignal], width: int = 50) -> str:
    """
    渲染信号强度分布直方图 / Render signal strength distribution histogram

    Args / 参数:
        signals: WiFi信号列表 / List of WiFi signals
        width: 图表宽度 / Chart width

    Returns / 返回:
        分布图字符串 / Distribution chart string
    """
    if not signals:
        return "  (无数据 / No data)"

    # 分组 / Group into bins
    bins = [
        ("极强/Excellent", -50, 0),
        ("强/Strong", -60, -50),
        ("中/Good", -70, -60),
        ("弱/Weak", -80, -70),
        ("极弱/V.Weak", -100, -80),
    ]

    counts = [0] * len(bins)
    for s in signals:
        for i, (_, low, high) in enumerate(bins):
            if low <= s.rssi < high or (i == 0 and s.rssi >= high):
                counts[i] += 1
                break

    max_count = max(counts) if max(counts) > 0 else 1

    lines: List[str] = []
    lines.append(f"  {colorize('信号强度分布 / Signal Strength Distribution', Colors.BOLD)}")
    lines.append("")

    for i, (label, _, _) in enumerate(bins):
        count = counts[i]
        bar_len = int(width * count / max_count) if max_count > 0 else 0
        bar = PROGRESS_FULL * bar_len + PROGRESS_EMPTY * (width - bar_len)

        color = signal_color(-50 + i * 10)
        lines.append(f"  {label:<16} {colorize(bar, color)} {count:>3}")

    lines.append(f"  {'─' * 16} {'─' * width} {'─' * 3}")
    lines.append(f"  {'总计/Total':<16} {PROGRESS_FULL * width} {len(signals):>3}")

    return "\n".join(lines)


# ============================================================
# 完整报告渲染 / Full Report Rendering
# ============================================================
def render_full_report(result: ScanResult, analysis: Optional[AnalysisResult] = None) -> str:
    """
    渲染完整报告 / Render full report

    Args / 参数:
        result: 扫描结果 / Scan result
        analysis: 分析结果 / Analysis result

    Returns / 返回:
        完整报告字符串 / Full report string
    """
    sections: List[str] = []

    # 摘要面板 / Summary panel
    sections.append(render_dashboard_summary(result, analysis))

    sections.append("")  # 空行分隔 / Blank line separator

    # 信号条形图 / Signal bars
    sections.append(render_signal_bars(result.signals))

    sections.append("")

    # 信道热力图 / Channel heatmap
    sections.append(render_channel_heatmap(result.signals))

    sections.append("")

    # 分布图 / Distribution
    sections.append(render_distribution(result.signals))

    return "\n".join(sections)
