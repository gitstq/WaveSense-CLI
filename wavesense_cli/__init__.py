"""
WaveSense-CLI - 轻量级终端无线信号智能感知与分析引擎
Lightweight Terminal Wireless Signal Intelligence & Analysis Engine
=====================================================================

一个零外部依赖的Python CLI工具，用于WiFi信号扫描、分析和可视化。
A zero-dependency Python CLI tool for WiFi signal scanning, analysis, and visualization.

核心功能 / Core Features:
    - 跨平台WiFi信号扫描 / Cross-platform WiFi signal scanning
    - 信号统计分析与异常检测 / Signal statistical analysis & anomaly detection
    - ASCII热力图与趋势图可视化 / ASCII heatmap & trend chart visualization
    - TUI实时仪表盘 / TUI real-time dashboard
    - 多格式报告导出（JSON/CSV/Markdown）/ Multi-format report export

使用示例 / Usage Examples:
    >>> from wavesense_cli import WiFiScanner
    >>> scanner = WiFiScanner()
    >>> result = scanner.scan()
    >>> print(f"发现 {result.signal_count} 个信号")

    >>> from wavesense_cli.analyzer import calculate_statistics
    >>> stats = calculate_statistics(result.signals)
    >>> print(f"平均信号强度: {stats.mean} dBm")
"""

__version__ = "1.0.0"
__author__ = "WaveSense-CLI Contributors"
__license__ = "MIT"

# 导出核心类和函数 / Export core classes and functions
from .models import (
    WiFiSignal,
    ScanResult,
    AnalysisResult,
    SignalHistory,
    SignalRecord,
    SignalStatistics,
    SignalLevel,
    classify_signal,
)
from .scanner import WiFiScanner
from .analyzer import (
    calculate_statistics,
    detect_anomalies,
    analyze_trend,
    estimate_distance,
    classify_signals,
    get_signal_summary,
)
from .visualizer import (
    render_heatmap,
    render_signal_bar,
    render_signal_chart,
    render_dashboard_summary,
    render_distribution,
    render_channel_heatmap,
)
from .exporter import export_report, export_json, export_csv, export_markdown
from .config import WaveSenseConfig, detect_platform, setup_logging

__all__ = [
    # 版本 / Version
    "__version__",
    # 数据模型 / Data models
    "WiFiSignal",
    "ScanResult",
    "AnalysisResult",
    "SignalHistory",
    "SignalRecord",
    "SignalStatistics",
    "SignalLevel",
    "classify_signal",
    # 扫描器 / Scanner
    "WiFiScanner",
    # 分析器 / Analyzer
    "calculate_statistics",
    "detect_anomalies",
    "analyze_trend",
    "estimate_distance",
    "classify_signals",
    "get_signal_summary",
    # 可视化 / Visualizer
    "render_heatmap",
    "render_signal_bar",
    "render_signal_chart",
    "render_dashboard_summary",
    "render_distribution",
    "render_channel_heatmap",
    # 导出 / Exporter
    "export_report",
    "export_json",
    "export_csv",
    "export_markdown",
    # 配置 / Config
    "WaveSenseConfig",
    "detect_platform",
    "setup_logging",
]
