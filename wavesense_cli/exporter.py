"""
WaveSense-CLI - 多格式导出引擎 / Multi-format Export Engine
=============================================================

支持将扫描数据和分析结果导出为多种格式。
Supports exporting scan data and analysis results to multiple formats.

支持格式 / Supported formats:
    - JSON: 结构化数据 / Structured data
    - CSV:  表格数据 / Tabular data
    - Markdown: 可读报告 / Readable report
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import (
    AnalysisResult,
    ScanResult,
    SignalHistory,
    SignalRecord,
    SignalStatistics,
    WiFiSignal,
)
from .utils import ensure_directory, format_timestamp, generate_filename

logger = logging.getLogger("wavesense.exporter")


# ============================================================
# 自定义异常 / Custom Exceptions
# ============================================================
class ExportError(Exception):
    """导出错误基类 / Base export error"""
    pass


class UnsupportedFormatError(ExportError):
    """不支持的格式错误 / Unsupported format error"""
    pass


# ============================================================
# JSON导出 / JSON Export
# ============================================================
def export_json(
    data: Any,
    filepath: str,
    indent: int = 2,
    ensure_ascii: bool = False,
) -> str:
    """
    导出数据为JSON文件 / Export data to JSON file
    ==============================================

    Args / 参数:
        data: 可导出的数据（需支持to_dict方法或为dict）/ Exportable data
        filepath: 输出文件路径 / Output file path
        indent: 缩进空格数 / Indent spaces
        ensure_ascii: 是否转义非ASCII字符 / Whether to escape non-ASCII characters

    Returns / 返回:
        输出文件路径 / Output file path

    Raises / 异常:
        ExportError: 导出失败 / Export failed
    """
    try:
        # 转换为字典 / Convert to dict
        if hasattr(data, "to_dict"):
            export_data = data.to_dict()
        elif isinstance(data, (list, tuple)):
            export_data = [
                item.to_dict() if hasattr(item, "to_dict") else item
                for item in data
            ]
        elif isinstance(data, dict):
            export_data = data
        else:
            export_data = {"data": str(data)}

        # 确保目录存在 / Ensure directory exists
        ensure_directory(filepath)

        # 写入文件 / Write file
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=indent, ensure_ascii=ensure_ascii)

        logger.info("JSON导出成功 / JSON export successful: %s", filepath)
        return filepath

    except (IOError, OSError, TypeError) as e:
        raise ExportError(f"JSON导出失败 / JSON export failed: {e}")


# ============================================================
# CSV导出 / CSV Export
# ============================================================
def export_csv(
    data: Any,
    filepath: str,
    delimiter: str = ",",
) -> str:
    """
    导出数据为CSV文件 / Export data to CSV file
    ==============================================

    支持的数据类型 / Supported data types:
        - ScanResult: 每行一个WiFi信号 / One WiFi signal per row
        - SignalHistory: 每行一条记录 / One record per row
        - List[WiFiSignal]: 信号列表 / Signal list

    Args / 参数:
        data: 可导出的数据 / Exportable data
        filepath: 输出文件路径 / Output file path
        delimiter: 分隔符 / Delimiter

    Returns / 返回:
        输出文件路径 / Output file path

    Raises / 异常:
        ExportError: 导出失败 / Export failed
    """
    try:
        # 确定数据源 / Determine data source
        signals: List[WiFiSignal] = []

        if isinstance(data, ScanResult):
            signals = data.signals
        elif isinstance(data, SignalHistory):
            # 将历史记录转换为信号格式 / Convert history records to signal format
            for record in data.records:
                signals.append(WiFiSignal(
                    ssid=record.ssid,
                    bssid=record.bssid,
                    rssi=record.rssi,
                    timestamp=record.timestamp,
                ))
        elif isinstance(data, list):
            signals = data
        else:
            raise ExportError(f"不支持的数据类型 / Unsupported data type: {type(data)}")

        if not signals:
            logger.warning("无数据可导出 / No data to export")
            ensure_directory(filepath)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("")
            return filepath

        # CSV字段 / CSV fields
        fieldnames = [
            "ssid", "bssid", "rssi", "rssi_percentage", "signal_level",
            "channel", "frequency", "security", "timestamp", "time_formatted",
        ]

        # 确保目录存在 / Ensure directory exists
        ensure_directory(filepath)

        # 写入CSV / Write CSV
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
            writer.writeheader()

            for signal in signals:
                from .utils import rssi_to_percentage
                writer.writerow({
                    "ssid": signal.ssid or "(隐藏/Hidden)",
                    "bssid": signal.bssid,
                    "rssi": signal.rssi,
                    "rssi_percentage": rssi_to_percentage(signal.rssi),
                    "signal_level": signal.signal_level.value,
                    "channel": signal.channel,
                    "frequency": signal.frequency,
                    "security": signal.security or "Open",
                    "timestamp": signal.timestamp,
                    "time_formatted": format_timestamp(signal.timestamp),
                })

        logger.info("CSV导出成功 / CSV export successful: %s (%d rows)", filepath, len(signals))
        return filepath

    except (IOError, OSError, csv.Error) as e:
        raise ExportError(f"CSV导出失败 / CSV export failed: {e}")


# ============================================================
# Markdown导出 / Markdown Export
# ============================================================
def export_markdown(
    data: Any,
    filepath: str,
    title: Optional[str] = None,
) -> str:
    """
    导出数据为Markdown报告 / Export data to Markdown report
    ===========================================================

    生成包含扫描结果和分析数据的可读Markdown报告。
    Generate a readable Markdown report containing scan results and analysis data.

    Args / 参数:
        data: 扫描结果或分析结果 / Scan result or analysis result
        filepath: 输出文件路径 / Output file path
        title: 报告标题 / Report title

    Returns / 返回:
        输出文件路径 / Output file path

    Raises / 异常:
        ExportError: 导出失败 / Export failed
    """
    try:
        md_lines: List[str] = []

        # 标题 / Title
        report_title = title or "WaveSense-CLI 信号分析报告 / Signal Analysis Report"
        md_lines.append(f"# {report_title}")
        md_lines.append("")

        # 元信息 / Meta info
        md_lines.append(f"> 生成时间 / Generated: {format_timestamp(data.scan_time) if hasattr(data, 'scan_time') else format_timestamp(0)}")
        md_lines.append(f"> 平台 / Platform: {getattr(data, 'platform', 'N/A')}")
        md_lines.append("")

        # 扫描结果 / Scan results
        if isinstance(data, ScanResult):
            md_lines = _render_scan_result_markdown(data, md_lines)

        # 确保目录存在 / Ensure directory exists
        ensure_directory(filepath)

        # 写入文件 / Write file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))

        logger.info("Markdown导出成功 / Markdown export successful: %s", filepath)
        return filepath

    except (IOError, OSError) as e:
        raise ExportError(f"Markdown导出失败 / Markdown export failed: {e}")


def _render_scan_result_markdown(result: ScanResult, lines: List[str]) -> List[str]:
    """
    渲染扫描结果为Markdown / Render scan result as Markdown

    Args / 参数:
        result: 扫描结果 / Scan result
        lines: 已有行 / Existing lines

    Returns / 返回:
        Markdown行列表 / Markdown line list
    """
    from .analyzer import calculate_statistics, get_signal_summary

    # 概览 / Overview
    lines.append("## 概览 / Overview")
    lines.append("")
    lines.append(f"| 指标 / Metric | 值 / Value |")
    lines.append(f"|---|---|")
    lines.append(f"| 发现信号数 / Signals Found | {result.signal_count} |")
    lines.append(f"| 扫描时间 / Scan Time | {format_timestamp(result.scan_time)} |")
    lines.append(f"| 扫描耗时 / Duration | {result.scan_duration:.2f}s |")
    lines.append(f"| 网络接口 / Interface | {result.interface or '自动/Auto'} |")
    lines.append("")

    if not result.signals:
        lines.append("> 未发现WiFi信号 / No WiFi signals detected")
        return lines

    # 统计信息 / Statistics
    stats = calculate_statistics(result.signals)
    lines.append("## 信号统计 / Signal Statistics")
    lines.append("")
    lines.append(f"| 统计项 / Statistic | 值 / Value |")
    lines.append(f"|---|---|")
    lines.append(f"| 平均值 / Mean | {stats.mean:.1f} dBm |")
    lines.append(f"| 中位数 / Median | {stats.median:.1f} dBm |")
    lines.append(f"| 标准差 / Std Dev | {stats.std_dev:.1f} dBm |")
    lines.append(f"| 最小值 / Min | {stats.min_val:.0f} dBm |")
    lines.append(f"| 最大值 / Max | {stats.max_val:.0f} dBm |")
    lines.append("")

    # 最强信号 / Strongest signal
    if result.strongest_signal:
        s = result.strongest_signal
        lines.append("## 最强信号 / Strongest Signal")
        lines.append("")
        lines.append(f"- **SSID**: {s.ssid or '(隐藏/Hidden)'}")
        lines.append(f"- **BSSID**: `{s.bssid}`")
        lines.append(f"- **RSSI**: {s.rssi} dBm ({s.signal_level.value})")
        lines.append(f"- **信道 / Channel**: {s.channel}")
        lines.append(f"- **加密 / Security**: {s.security or 'Open'}")
        lines.append("")

    # 信号列表 / Signal list
    lines.append("## 信号列表 / Signal List")
    lines.append("")
    lines.append("| # | SSID | BSSID | RSSI (dBm) | 信道/Ch | 加密/Security | 等级/Level |")
    lines.append("|---|------|-------|------------|---------|---------------|------------|")

    sorted_signals = sorted(result.signals, key=lambda s: s.rssi, reverse=True)
    for i, signal in enumerate(sorted_signals, 1):
        ssid = signal.ssid or "(隐藏/Hidden)"
        lines.append(
            f"| {i} | {ssid} | `{signal.bssid}` | {signal.rssi} | "
            f"{signal.channel} | {signal.security or 'Open'} | {signal.signal_level.value} |"
        )
    lines.append("")

    # 信道分析 / Channel analysis
    from .analyzer import analyze_channels
    channel_info = analyze_channels(result.signals)
    if channel_info["total_channels_used"] > 0:
        lines.append("## 信道分析 / Channel Analysis")
        lines.append("")
        lines.append(f"- 使用信道数 / Channels Used: {channel_info['total_channels_used']}")
        lines.append(f"- 最拥挤信道 / Most Crowded: Ch {channel_info['most_crowded']}")
        lines.append(f"- 推荐信道 / Recommended: Ch {channel_info['recommended_channel']}")
        lines.append("")

    return lines


# ============================================================
# 统一导出接口 / Unified Export Interface
# ============================================================
def export_report(
    data: Any,
    format: str = "json",
    filepath: Optional[str] = None,
    output_dir: str = "./reports",
    prefix: str = "wavesense_report",
    include_timestamp: bool = True,
    **kwargs: Any,
) -> str:
    """
    统一导出接口 / Unified export interface
    ==========================================
    根据指定格式导出数据。

    Args / 参数:
        data: 可导出的数据 / Exportable data
        format: 导出格式（json/csv/markdown）/ Export format
        filepath: 输出文件路径（可选）/ Output file path (optional)
        output_dir: 输出目录 / Output directory
        prefix: 文件名前缀 / Filename prefix
        include_timestamp: 文件名包含时间戳 / Include timestamp in filename
        **kwargs: 额外参数 / Additional parameters

    Returns / 返回:
        输出文件路径 / Output file path

    Raises / 异常:
        UnsupportedFormatError: 不支持的格式 / Unsupported format
        ExportError: 导出失败 / Export failed
    """
    format = format.lower().strip()

    # 确定文件路径 / Determine file path
    if not filepath:
        ext_map = {
            "json": "json",
            "csv": "csv",
            "markdown": "md",
            "md": "md",
        }
        ext = ext_map.get(format, "txt")
        filename = generate_filename(prefix, ext, include_timestamp)
        filepath = os.path.join(output_dir, filename)

    # 根据格式调用对应导出函数 / Call corresponding export function by format
    if format == "json":
        return export_json(data, filepath, **kwargs)
    elif format == "csv":
        return export_csv(data, filepath, **kwargs)
    elif format in ("markdown", "md"):
        return export_markdown(data, filepath, **kwargs)
    else:
        raise UnsupportedFormatError(
            f"不支持的导出格式: {format} / Unsupported export format: {format}. "
            f"支持: json, csv, markdown/md / Supported: json, csv, markdown/md"
        )


def export_to_string(data: Any, format: str = "json") -> str:
    """
    导出数据到字符串 / Export data to string
    ===========================================

    Args / 参数:
        data: 可导出的数据 / Exportable data
        format: 导出格式 / Export format

    Returns / 返回:
        格式化的字符串 / Formatted string
    """
    if format == "json":
        if hasattr(data, "to_dict"):
            return json.dumps(data.to_dict(), indent=2, ensure_ascii=False)
        return json.dumps(data, indent=2, ensure_ascii=False)
    elif format == "csv":
        # 直接生成CSV字符串 / Generate CSV string directly
        if isinstance(data, ScanResult):
            signals = data.signals
        elif isinstance(data, list):
            signals = data
        else:
            signals = []

        if not signals:
            return ""

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["SSID", "BSSID", "RSSI", "Channel", "Security", "Level"])
        for s in signals:
            writer.writerow([
                s.ssid or "(隐藏/Hidden)", s.bssid, s.rssi,
                s.channel, s.security or "Open", s.signal_level.value,
            ])
        return output.getvalue()
    else:
        return str(data)
