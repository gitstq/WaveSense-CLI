"""
WaveSense-CLI - 工具函数模块 / Utility Functions Module
=======================================================

提供项目中各模块共用的工具函数。
Provides utility functions shared across project modules.

包含：时间格式化、信号转换、终端控制、数据验证等。
Contains: time formatting, signal conversion, terminal control, data validation, etc.
"""

from __future__ import annotations

import math
import os
import re
import struct
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


# ============================================================
# 时间工具 / Time Utilities
# ============================================================
def format_timestamp(ts: float, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化时间戳 / Format timestamp

    Args / 参数:
        ts: Unix时间戳 / Unix timestamp
        fmt: 格式字符串 / Format string

    Returns / 返回:
        格式化的时间字符串 / Formatted time string
    """
    try:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return dt.strftime(fmt)
    except (OSError, ValueError):
        return "N/A"


def timestamp_now() -> float:
    """获取当前Unix时间戳 / Get current Unix timestamp"""
    return time.time()


def duration_str(seconds: float) -> str:
    """
    将秒数格式化为可读字符串 / Format seconds to readable string

    Args / 参数:
        seconds: 秒数 / Number of seconds

    Returns / 返回:
        格式化的持续时间字符串 / Formatted duration string
    """
    if seconds < 0.001:
        return f"{seconds * 1000000:.0f}us"
    elif seconds < 1:
        return f"{seconds * 1000:.1f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.0f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"


# ============================================================
# 信号工具 / Signal Utilities
# ============================================================
def rssi_to_percentage(rssi: int) -> int:
    """
    将RSSI值转换为信号质量百分比 / Convert RSSI to signal quality percentage

    RSSI范围通常为 -100 到 0 dBm。
    RSSI range is typically -100 to 0 dBm.

    Args / 参数:
        rssi: 信号强度（dBm）/ Signal strength in dBm

    Returns / 返回:
        信号质量百分比（0-100）/ Signal quality percentage (0-100)
    """
    # 限制范围 / Clamp range
    rssi = max(-100, min(0, rssi))
    # 线性映射 / Linear mapping
    return int(100 * (rssi + 100) / 100)


def rssi_to_quality(rssi: int) -> str:
    """
    将RSSI值转换为质量描述 / Convert RSSI to quality description

    Args / 参数:
        rssi: 信号强度（dBm）/ Signal strength in dBm

    Returns / 返回:
        质量描述字符串 / Quality description string
    """
    if rssi >= -50:
        return "极强/Excellent"
    elif rssi >= -60:
        return "强/Strong"
    elif rssi >= -70:
        return "中/Good"
    elif rssi >= -80:
        return "弱/Weak"
    else:
        return "极弱/Very Weak"


def estimate_distance_fspl(rssi: int, freq_mhz: int = 2412) -> float:
    """
    基于自由空间路径损耗模型（FSPL）估算距离
    Estimate distance based on Free Space Path Loss (FSPL) model
    ================================================================

    公式 / Formula:
        FSPL(dB) = 20*log10(d) + 20*log10(f) + 20*log10(4*pi/c)
        d = 10^((|RSSI| - A) / (10 * n))

    其中 / Where:
        A = 20*log10(4*pi/c) + 20*log10(f)  (在1米处的参考损耗)
        n = 路径损耗指数 / Path loss exponent (2.0 for free space)

    注意：此为粗略估算，实际环境因素会影响结果。
    Note: This is a rough estimate; actual environmental factors affect results.

    Args / 参数:
        rssi: 信号强度（dBm）/ Signal strength in dBm
        freq_mhz: 频率（MHz）/ Frequency in MHz (default: 2412 for 2.4GHz ch1)

    Returns / 返回:
        估算距离（米）/ Estimated distance in meters
    """
    if rssi >= 0:
        return 0.0

    # 1米处的参考RSSI值（经验值）/ Reference RSSI at 1 meter (empirical)
    # 2.4GHz: 约 -40 dBm, 5GHz: 约 -47 dBm
    if freq_mhz >= 5000:
        a_ref = -47  # 5GHz参考值 / 5GHz reference
    else:
        a_ref = -40  # 2.4GHz参考值 / 2.4GHz reference

    # 路径损耗指数 / Path loss exponent
    n = 2.7  # 室内环境典型值 / Typical indoor value

    try:
        distance = 10 ** ((abs(rssi) - abs(a_ref)) / (10 * n))
        return round(distance, 2)
    except (OverflowError, ZeroDivisionError):
        return 999.9


def channel_to_frequency(channel: int) -> int:
    """
    将WiFi信道转换为频率 / Convert WiFi channel to frequency

    Args / 参数:
        channel: 信道号 / Channel number

    Returns / 返回:
        频率（MHz）/ Frequency in MHz
    """
    # 2.4GHz频段 / 2.4GHz band
    if 1 <= channel <= 14:
        return 2412 + (channel - 1) * 5
    # 5GHz频段（部分信道）/ 5GHz band (partial channels)
    elif 36 <= channel <= 165:
        return 5000 + channel * 5
    return 0


def frequency_to_channel(freq: int) -> int:
    """
    将频率转换为WiFi信道 / Convert frequency to WiFi channel

    Args / 参数:
        freq: 频率（MHz）/ Frequency in MHz

    Returns / 返回:
        信道号 / Channel number
    """
    # 2.4GHz频段 / 2.4GHz band
    if 2412 <= freq <= 2484:
        return (freq - 2412) // 5 + 1
    # 5GHz频段 / 5GHz band
    elif 5000 <= freq <= 5825:
        return (freq - 5000) // 5
    return 0


# ============================================================
# 终端工具 / Terminal Utilities
# ============================================================
def get_terminal_size() -> Tuple[int, int]:
    """
    获取终端尺寸 / Get terminal size

    Returns / 返回:
        (宽度, 高度) 元组 / (width, height) tuple
    """
    try:
        size = os.get_terminal_size()
        return size.columns, size.lines
    except (OSError, AttributeError):
        return 80, 24


def clear_screen() -> None:
    """清屏 / Clear screen"""
    # ANSI转义序列清屏 / ANSI escape sequence to clear screen
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def move_cursor(row: int, col: int) -> None:
    """
    移动光标到指定位置 / Move cursor to specified position

    Args / 参数:
        row: 行号（从0开始）/ Row number (0-indexed)
        col: 列号（从0开始）/ Column number (0-indexed)
    """
    sys.stdout.write(f"\033[{row + 1};{col + 1}H")
    sys.stdout.flush()


def hide_cursor() -> None:
    """隐藏光标 / Hide cursor"""
    sys.stdout.write("\033[?25l")
    sys.stdout.flush()


def show_cursor() -> None:
    """显示光标 / Show cursor"""
    sys.stdout.write("\033[?25h")
    sys.stdout.flush()


# ============================================================
# ANSI颜色工具 / ANSI Color Utilities
# ============================================================
class Colors:
    """ANSI颜色代码 / ANSI color codes"""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    UNDERLINE = "\033[4m"

    # 前景色 / Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # 亮色 / Bright colors
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # 背景色 / Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


def colorize(text: str, color: str) -> str:
    """
    为文本添加ANSI颜色 / Add ANSI color to text

    Args / 参数:
        text: 原始文本 / Original text
        color: ANSI颜色代码 / ANSI color code

    Returns / 返回:
        着色后的文本 / Colored text
    """
    # 如果输出不是终端，不添加颜色 / Don't add colors if output is not a terminal
    if not sys.stdout.isatty():
        return text
    return f"{color}{text}{Colors.RESET}"


def signal_color(rssi: int) -> str:
    """
    根据信号强度返回对应颜色 / Return color based on signal strength

    Args / 参数:
        rssi: 信号强度（dBm）/ Signal strength in dBm

    Returns / 返回:
        ANSI颜色代码 / ANSI color code
    """
    if rssi >= -50:
        return Colors.BRIGHT_GREEN
    elif rssi >= -60:
        return Colors.GREEN
    elif rssi >= -70:
        return Colors.YELLOW
    elif rssi >= -80:
        return Colors.BRIGHT_RED
    else:
        return Colors.RED


# ============================================================
# 数据验证工具 / Data Validation Utilities
# ============================================================
def validate_rssi(rssi: Any) -> int:
    """
    验证并规范化RSSI值 / Validate and normalize RSSI value

    Args / 参数:
        rssi: 待验证的值 / Value to validate

    Returns / 返回:
        规范化后的RSSI值 / Normalized RSSI value

    Raises / 异常:
        ValueError: 值超出有效范围 / Value out of valid range
    """
    try:
        rssi_int = int(rssi)
    except (TypeError, ValueError):
        raise ValueError(f"无效的RSSI值: {rssi} / Invalid RSSI value: {rssi}")

    if not -100 <= rssi_int <= 0:
        raise ValueError(f"RSSI值超出范围(-100~0): {rssi_int} / RSSI out of range: {rssi_int}")

    return rssi_int


def validate_bssid(bssid: str) -> str:
    """
    验证BSSID（MAC地址）格式 / Validate BSSID (MAC address) format

    Args / 参数:
        bssid: MAC地址字符串 / MAC address string

    Returns / 返回:
        规范化后的MAC地址 / Normalized MAC address

    Raises / 异常:
        ValueError: 格式无效 / Invalid format
    """
    bssid = bssid.strip().upper()
    # 支持冒号和连字符分隔 / Support colon and hyphen separators
    pattern = r"^([0-9A-F]{2}[:-]){5}[0-9A-F]{2}$"
    if not re.match(pattern, bssid):
        raise ValueError(f"无效的BSSID格式: {bssid} / Invalid BSSID format: {bssid}")
    # 统一为冒号分隔 / Normalize to colon separator
    return bssid.replace("-", ":")


def validate_channel(channel: Any) -> int:
    """
    验证WiFi信道号 / Validate WiFi channel number

    Args / 参数:
        channel: 信道号 / Channel number

    Returns / 返回:
        验证后的信道号 / Validated channel number

    Raises / 异常:
        ValueError: 信道号无效 / Invalid channel number
    """
    try:
        ch = int(channel)
    except (TypeError, ValueError):
        raise ValueError(f"无效的信道号: {channel} / Invalid channel number: {channel}")

    valid_channels = set(range(1, 15)) | set(range(36, 166))
    if ch not in valid_channels:
        raise ValueError(f"不支持的信道号: {ch} / Unsupported channel: {ch}")

    return ch


# ============================================================
# 命令执行工具 / Command Execution Utilities
# ============================================================
def run_command(
    cmd: List[str],
    timeout: float = 10.0,
    encoding: str = "utf-8",
    shell: bool = False,
) -> Tuple[int, str, str]:
    """
    执行系统命令并返回结果 / Execute system command and return results

    Args / 参数:
        cmd: 命令及参数列表 / Command and argument list
        timeout: 超时时间（秒）/ Timeout in seconds
        encoding: 输出编码 / Output encoding
        shell: 是否使用shell执行 / Whether to use shell

    Returns / 返回:
        (返回码, 标准输出, 标准错误) 元组 / (return code, stdout, stderr) tuple
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=shell,
            encoding=encoding,
            errors="replace",
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", f"命令超时({timeout}s) / Command timed out({timeout}s)"
    except FileNotFoundError:
        return -1, "", f"命令未找到: {cmd[0]} / Command not found: {cmd[0]}"
    except OSError as e:
        return -1, "", f"执行错误: {e} / Execution error: {e}"


# ============================================================
# 数学工具 / Math Utilities
# ============================================================
def linear_regression(x: List[float], y: List[float]) -> Tuple[float, float]:
    """
    简单线性回归 / Simple Linear Regression
    =========================================
    使用最小二乘法计算线性回归参数。
    Calculate linear regression parameters using least squares method.

    y = slope * x + intercept

    Args / 参数:
        x: 自变量列表 / Independent variable list
        y: 因变量列表 / Dependent variable list

    Returns / 返回:
        (斜率, 截距) 元组 / (slope, intercept) tuple
    """
    n = len(x)
    if n < 2 or n != len(y):
        return 0.0, 0.0

    sum_x = sum(x)
    sum_y = sum(y)
    sum_xy = sum(xi * yi for xi, yi in zip(x, y))
    sum_x2 = sum(xi * xi for xi in x)

    denominator = n * sum_x2 - sum_x * sum_x
    if denominator == 0:
        return 0.0, sum_y / n

    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n

    return slope, intercept


def calculate_r_squared(x: List[float], y: List[float]) -> float:
    """
    计算R-squared（决定系数）/ Calculate R-squared (coefficient of determination)

    Args / 参数:
        x: 自变量列表 / Independent variable list
        y: 因变量列表 / Dependent variable list

    Returns / 返回:
        R-squared值（0-1）/ R-squared value (0-1)
    """
    n = len(x)
    if n < 2:
        return 0.0

    slope, intercept = linear_regression(x, y)
    y_mean = sum(y) / n

    ss_total = sum((yi - y_mean) ** 2 for yi in y)
    if ss_total == 0:
        return 1.0

    ss_residual = sum((yi - (slope * xi + intercept)) ** 2 for xi, yi in zip(x, y))
    return max(0.0, 1.0 - ss_residual / ss_total)


# ============================================================
# 文件工具 / File Utilities
# ============================================================
def ensure_directory(filepath: str) -> None:
    """
    确保文件所在目录存在 / Ensure the directory of the file exists

    Args / 参数:
        filepath: 文件路径 / File path
    """
    directory = os.path.dirname(filepath)
    if directory:
        os.makedirs(directory, exist_ok=True)


def generate_filename(prefix: str, extension: str, include_timestamp: bool = True) -> str:
    """
    生成带时间戳的文件名 / Generate filename with timestamp

    Args / 参数:
        prefix: 文件名前缀 / Filename prefix
        extension: 文件扩展名 / File extension
        include_timestamp: 是否包含时间戳 / Whether to include timestamp

    Returns / 返回:
        生成的文件名 / Generated filename
    """
    if include_timestamp:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{prefix}_{ts}.{extension}"
    return f"{prefix}.{extension}"
