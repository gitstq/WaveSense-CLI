"""
WaveSense-CLI - 命令行接口 / Command Line Interface
=====================================================

使用argparse构建的CLI命令解析，提供完整的子命令体系。
CLI command parsing built with argparse, providing a complete subcommand system.

命令 / Commands:
    wavesense scan          扫描一次WiFi信号 / Scan WiFi signals once
    wavesense monitor       持续监控模式 / Continuous monitoring mode
    wavesense dashboard     TUI仪表盘 / TUI dashboard
    wavesense analyze       分析历史数据 / Analyze historical data
    wavesense report        生成报告 / Generate report
    wavesense heatmap       显示信号热力图 / Display signal heatmap

全局参数 / Global options:
    --format, -f    输出格式 / Output format (json, csv, markdown)
    --output, -o    输出文件路径 / Output file path
    --interface, -i 网络接口 / Network interface
    --verbose, -v   详细输出 / Verbose output
    --json          JSON格式输出 / JSON format output
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import List, Optional

from . import __version__
from .analyzer import (
    analyze_channels,
    analyze_scan_result,
    calculate_statistics,
    detect_anomalies,
    get_signal_summary,
)
from .config import get_config, setup_logging
from .dashboard import Dashboard, run_simple_dashboard
from .exporter import export_report
from .models import SignalHistory, SignalRecord
from .scanner import WiFiScanner
from .utils import Colors, colorize, format_timestamp, get_terminal_size
from .visualizer import (
    render_channel_heatmap,
    render_dashboard_summary,
    render_distribution,
    render_full_report,
    render_signal_bars,
    render_signal_chart,
)


# ============================================================
# CLI应用类 / CLI Application Class
# ============================================================
class WaveSenseCLI:
    """
    WaveSense CLI应用 / WaveSense CLI Application
    ==============================================
    封装所有CLI命令的处理逻辑。
    Encapsulates all CLI command processing logic.
    """

    def __init__(self) -> None:
        """初始化CLI / Initialize CLI"""
        self._parser = self._build_parser()
        self._logger = logging.getLogger("wavesense.cli")

    # ============================================================
    # 参数解析器构建 / Argument Parser Building
    # ============================================================
    def _build_parser(self) -> argparse.ArgumentParser:
        """
        构建完整的参数解析器 / Build complete argument parser
        ======================================================
        """
        parser = argparse.ArgumentParser(
            prog="wavesense",
            description=(
                "WaveSense-CLI - 轻量级终端无线信号智能感知与分析引擎\n"
                "Lightweight Terminal Wireless Signal Intelligence & Analysis Engine"
            ),
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=(
                "\n使用示例 / Usage Examples:\n"
                "  wavesense scan                    扫描WiFi信号 / Scan WiFi signals\n"
                "  wavesense scan -v                  详细扫描 / Verbose scan\n"
                "  wavesense scan --json              JSON格式输出 / JSON output\n"
                "  wavesense monitor -i 5             每5秒监控 / Monitor every 5s\n"
                "  wavesense dashboard                TUI仪表盘 / TUI dashboard\n"
                "  wavesense report -f markdown -o report.md  生成Markdown报告 / Generate MD report\n"
                "  wavesense heatmap                  显示信道热力图 / Show channel heatmap\n"
                "\n信号强度等级 / Signal Levels:\n"
                "  极强/Excellent: -30~-50 dBm  强/Strong: -50~-60 dBm\n"
                "  中/Good: -60~-70 dBm  弱/Weak: -70~-80 dBm  极弱/V.Weak: <-80 dBm\n"
            ),
        )

        parser.add_argument(
            "-V", "--version",
            action="version",
            version=f"WaveSense-CLI v{__version__}",
        )

        # 全局可选参数 / Global optional arguments
        parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            default=False,
            help="详细输出模式 / Verbose output mode",
        )

        # 子命令 / Subcommands
        subparsers = parser.add_subparsers(
            dest="command",
            help="可用命令 / Available commands",
            metavar="COMMAND",
        )

        # --- scan 命令 / scan command ---
        scan_parser = subparsers.add_parser(
            "scan",
            help="扫描WiFi信号 / Scan WiFi signals",
            description="扫描周围WiFi信号并显示结果 / Scan surrounding WiFi signals and display results",
        )
        scan_parser.add_argument(
            "-i", "--interface",
            type=str, default="",
            help="指定网络接口 / Specify network interface",
        )
        scan_parser.add_argument(
            "-f", "--format",
            type=str, default="",
            choices=["json", "csv", "markdown"],
            help="输出格式 / Output format",
        )
        scan_parser.add_argument(
            "-o", "--output",
            type=str, default="",
            help="输出文件路径 / Output file path",
        )
        scan_parser.add_argument(
            "--json",
            action="store_true",
            default=False,
            help="JSON格式输出 / JSON format output",
        )

        # --- monitor 命令 / monitor command ---
        monitor_parser = subparsers.add_parser(
            "monitor",
            help="持续监控模式 / Continuous monitoring mode",
            description="持续扫描并监控WiFi信号变化 / Continuously scan and monitor WiFi signal changes",
        )
        monitor_parser.add_argument(
            "-i", "--interval",
            type=float, default=5.0,
            help="扫描间隔秒数 / Scan interval in seconds (default: 5)",
        )
        monitor_parser.add_argument(
            "-n", "--count",
            type=int, default=0,
            help="最大扫描次数（0=无限）/ Max scan count (0=unlimited)",
        )
        monitor_parser.add_argument(
            "--interface",
            type=str, default="",
            help="指定网络接口 / Specify network interface",
        )

        # --- dashboard 命令 / dashboard command ---
        dash_parser = subparsers.add_parser(
            "dashboard",
            help="TUI仪表盘 / TUI dashboard",
            description="启动终端实时仪表盘界面 / Launch terminal real-time dashboard",
        )
        dash_parser.add_argument(
            "-i", "--interval",
            type=float, default=2.0,
            help="刷新间隔秒数 / Refresh interval in seconds (default: 2)",
        )
        dash_parser.add_argument(
            "--simple",
            action="store_true",
            default=False,
            help="简单模式（不依赖select）/ Simple mode (no select dependency)",
        )

        # --- analyze 命令 / analyze command ---
        analyze_parser = subparsers.add_parser(
            "analyze",
            help="分析信号数据 / Analyze signal data",
            description="分析扫描数据，包括统计、异常检测和趋势分析 / Analyze scan data including statistics, anomaly detection, and trend analysis",
        )
        analyze_parser.add_argument(
            "--file",
            type=str, default="",
            help="历史数据文件路径 / History data file path",
        )
        analyze_parser.add_argument(
            "--threshold",
            type=float, default=2.0,
            help="异常检测Z-Score阈值 / Anomaly detection Z-Score threshold (default: 2.0)",
        )

        # --- report 命令 / report command ---
        report_parser = subparsers.add_parser(
            "report",
            help="生成报告 / Generate report",
            description="生成信号分析报告并导出 / Generate signal analysis report and export",
        )
        report_parser.add_argument(
            "-f", "--format",
            type=str, default="markdown",
            choices=["json", "csv", "markdown"],
            help="报告格式 / Report format (default: markdown)",
        )
        report_parser.add_argument(
            "-o", "--output",
            type=str, default="",
            help="输出文件路径 / Output file path",
        )
        report_parser.add_argument(
            "--dir",
            type=str, default="./reports",
            help="输出目录 / Output directory (default: ./reports)",
        )

        # --- heatmap 命令 / heatmap command ---
        heatmap_parser = subparsers.add_parser(
            "heatmap",
            help="显示信号热力图 / Display signal heatmap",
            description="显示WiFi信道使用热力图 / Display WiFi channel usage heatmap",
        )

        return parser

    # ============================================================
    # 命令执行 / Command Execution
    # ============================================================
    def run(self, args: Optional[List[str]] = None) -> int:
        """
        运行CLI / Run CLI

        Args / 参数:
            args: 命令行参数（None则使用sys.argv）/ Command line arguments

        Returns / 返回:
            退出码 / Exit code (0=success, non-zero=error)
        """
        parsed = self._parser.parse_args(args)

        # 设置日志级别 / Set log level
        if parsed.verbose or getattr(parsed, "json", False):
            log_level = "DEBUG"
        else:
            log_level = "INFO"
        setup_logging(log_level)

        # 无命令时显示帮助 / Show help when no command
        if not parsed.command:
            self._parser.print_help()
            return 0

        # 分发命令 / Dispatch command
        try:
            command_map = {
                "scan": self._cmd_scan,
                "monitor": self._cmd_monitor,
                "dashboard": self._cmd_dashboard,
                "analyze": self._cmd_analyze,
                "report": self._cmd_report,
                "heatmap": self._cmd_heatmap,
            }

            handler = command_map.get(parsed.command)
            if handler:
                return handler(parsed)
            else:
                self._parser.print_help()
                return 1

        except KeyboardInterrupt:
            print(colorize("\n操作已取消 / Operation cancelled.", Colors.DIM))
            return 130
        except Exception as e:
            self._logger.error("命令执行失败 / Command execution failed: %s", e, exc_info=True)
            print(colorize(f"\n错误 / Error: {e}", Colors.BRIGHT_RED), file=sys.stderr)
            return 1

    # ============================================================
    # scan 命令处理 / scan Command Handler
    # ============================================================
    def _cmd_scan(self, args: argparse.Namespace) -> int:
        """
        处理scan命令 / Handle scan command
        """
        scanner = WiFiScanner(interface=getattr(args, "interface", ""))

        # 执行扫描 / Perform scan
        result = scanner.scan(use_cache=False)

        # JSON输出模式 / JSON output mode
        if getattr(args, "json", False) or getattr(args, "format", "") == "json":
            print(result.to_json())
            return 0

        # 文件导出 / File export
        if getattr(args, "output", ""):
            fmt = getattr(args, "format", "") or "json"
            export_report(result, format=fmt, filepath=args.output)
            print(colorize(f"结果已导出 / Result exported to: {args.output}", Colors.GREEN))
            return 0

        # 终端输出 / Terminal output
        if not result.signals:
            print(colorize("  未发现WiFi信号 / No WiFi signals detected.", Colors.YELLOW))
            if result.error:
                print(colorize(f"  错误信息 / Error: {result.error}", Colors.RED))
            return 0

        # 显示扫描结果 / Display scan results
        print(colorize(f"\n  WaveSense-CLI 扫描结果 / Scan Results", Colors.BOLD + Colors.BRIGHT_CYAN))
        print(colorize(f"  {'─' * 60}", Colors.DIM))
        print(f"  发现 {colorize(str(result.signal_count), Colors.BRIGHT_GREEN)} 个WiFi信号 / signals found")
        print(f"  扫描时间 / Time: {format_timestamp(result.scan_time)}")
        if result.scan_duration > 0:
            print(f"  耗时 / Duration: {result.scan_duration:.2f}s")
        print()

        # 信号列表 / Signal list
        print(render_signal_bars(result.signals))

        # 统计信息 / Statistics
        if args.verbose:
            print()
            stats = calculate_statistics(result.signals)
            print(colorize("  统计信息 / Statistics:", Colors.BOLD))
            print(f"    均值/Mean: {stats.mean:.1f} dBm")
            print(f"    中位/Median: {stats.median:.1f} dBm")
            print(f"    标准差/Std: {stats.std_dev:.1f} dBm")
            print(f"    范围/Range: {stats.min_val:.0f} ~ {stats.max_val:.0f} dBm")

        return 0

    # ============================================================
    # monitor 命令处理 / monitor Command Handler
    # ============================================================
    def _cmd_monitor(self, args: argparse.Namespace) -> int:
        """
        处理monitor命令 / Handle monitor command
        """
        scanner = WiFiScanner(interface=getattr(args, "interface", ""))
        history = SignalHistory()
        scan_count = 0

        print(colorize(
            f"\n  WaveSense-CLI 持续监控 / Continuous Monitoring",
            Colors.BOLD + Colors.BRIGHT_CYAN,
        ))
        print(colorize(
            f"  间隔/Interval: {args.interval}s | 按Ctrl+C退出 / Press Ctrl+C to quit\n",
            Colors.DIM,
        ))

        try:
            scanner.monitor(
                callback=lambda result: self._monitor_callback(result, history, scan_count),
                interval=args.interval,
                max_scans=args.count if args.count > 0 else None,
            )
        except KeyboardInterrupt:
            pass

        print(colorize(f"\n  监控结束 / Monitoring ended.", Colors.DIM))
        return 0

    def _monitor_callback(
        self, result, history: SignalHistory, scan_count: int
    ) -> None:
        """监控回调函数 / Monitor callback function"""
        scan_count += 1

        # 更新历史 / Update history
        for signal in result.signals:
            history.add_record(SignalRecord(
                ssid=signal.ssid,
                bssid=signal.bssid,
                rssi=signal.rssi,
                timestamp=signal.timestamp,
            ))

        # 简洁输出 / Concise output
        timestamp = format_timestamp(result.scan_time, "%H:%M:%S")
        count = result.signal_count
        strongest = f"{result.strongest_signal.rssi} dBm" if result.strongest_signal else "N/A"

        print(
            f"  [{timestamp}] #{scan_count} | "
            f"信号/Signals: {count} | "
            f"最强/Strongest: {strongest}"
        )

        # 异常检测 / Anomaly detection
        if history.record_count >= 5:
            anomalies = detect_anomalies(history)
            for anomaly in anomalies:
                print(colorize(
                    f"  ⚠ 异常/Anomaly: {anomaly.ssid or anomaly.bssid} - {anomaly.description}",
                    Colors.BRIGHT_RED,
                ))

    # ============================================================
    # dashboard 命令处理 / dashboard Command Handler
    # ============================================================
    def _cmd_dashboard(self, args: argparse.Namespace) -> int:
        """
        处理dashboard命令 / Handle dashboard command
        """
        scanner = WiFiScanner()

        if args.simple:
            run_simple_dashboard(scanner=scanner, interval=args.interval)
        else:
            dashboard = Dashboard(scanner=scanner, refresh_interval=args.interval)
            dashboard.run()

        return 0

    # ============================================================
    # analyze 命令处理 / analyze Command Handler
    # ============================================================
    def _cmd_analyze(self, args: argparse.Namespace) -> int:
        """
        处理analyze命令 / Handle analyze command
        """
        # 如果有历史文件，加载分析 / Load and analyze if history file exists
        if getattr(args, "file", ""):
            try:
                with open(args.file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                history = SignalHistory()
                for record in data.get("records", []):
                    history.add_record(SignalRecord(**record))

                from .analyzer import analyze_history
                result = analyze_history(history)

                if getattr(args, "json", False):
                    print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
                else:
                    self._print_analysis_result(result)

                return 0
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(colorize(f"无法加载历史文件 / Cannot load history file: {e}", Colors.RED))
                return 1

        # 否则执行一次扫描并分析 / Otherwise scan once and analyze
        scanner = WiFiScanner()
        result = scanner.scan(use_cache=False)

        if not result.signals:
            print(colorize("  无信号数据可分析 / No signal data to analyze.", Colors.YELLOW))
            return 0

        analysis = analyze_scan_result(result)

        if getattr(args, "json", False):
            print(json.dumps(analysis.to_dict(), indent=2, ensure_ascii=False))
        else:
            self._print_analysis_result(analysis)
            print()
            print(render_signal_bars(result.signals))
            print()
            print(render_distribution(result.signals))
            print()
            print(render_channel_heatmap(result.signals))

        return 0

    def _print_analysis_result(self, analysis) -> None:
        """打印分析结果 / Print analysis result"""
        print(colorize("\n  分析结果 / Analysis Results", Colors.BOLD + Colors.BRIGHT_CYAN))
        print(colorize(f"  {'─' * 50}", Colors.DIM))

        if analysis.statistics:
            stats = analysis.statistics
            print(f"\n  统计 / Statistics:")
            print(f"    样本数 / Count: {stats.count}")
            print(f"    均值 / Mean:   {stats.mean:.1f} dBm")
            print(f"    中位 / Median: {stats.median:.1f} dBm")
            print(f"    标准差 / Std:   {stats.std_dev:.1f} dBm")
            print(f"    方差 / Var:    {stats.variance:.1f}")
            print(f"    范围 / Range:  {stats.min_val:.0f} ~ {stats.max_val:.0f} dBm")

        if analysis.anomalies:
            print(f"\n  {colorize(f'异常 / Anomalies ({len(analysis.anomalies)}):', Colors.BRIGHT_RED)}")
            for anomaly in analysis.anomalies[:10]:
                print(f"    - {anomaly.ssid or anomaly.bssid}: {anomaly.description}")

        if analysis.trends:
            print(f"\n  趋势 / Trends:")
            for bssid, trend in analysis.trends.items():
                direction_map = {
                    "rising": "↑ 上升/Rising",
                    "falling": "↓ 下降/Falling",
                    "stable": "→ 稳定/Stable",
                }
                direction = direction_map.get(trend.direction, trend.direction)
                print(f"    {bssid}: {direction} (R²={trend.confidence:.2f})")

    # ============================================================
    # report 命令处理 / report Command Handler
    # ============================================================
    def _cmd_report(self, args: argparse.Namespace) -> int:
        """
        处理report命令 / Handle report command
        """
        scanner = WiFiScanner()
        result = scanner.scan(use_cache=False)

        if not result.signals:
            print(colorize("  无信号数据，无法生成报告 / No signal data, cannot generate report.", Colors.YELLOW))
            return 0

        # 确定输出路径 / Determine output path
        filepath = args.output or ""
        output_dir = args.dir

        # 生成报告 / Generate report
        output_path = export_report(
            data=result,
            format=args.format,
            filepath=filepath if filepath else None,
            output_dir=output_dir,
            prefix="wavesense_report",
        )

        print(colorize(f"  报告已生成 / Report generated: {output_path}", Colors.GREEN))
        return 0

    # ============================================================
    # heatmap 命令处理 / heatmap Command Handler
    # ============================================================
    def _cmd_heatmap(self, args: argparse.Namespace) -> int:
        """
        处理heatmap命令 / Handle heatmap command
        """
        scanner = WiFiScanner()
        result = scanner.scan(use_cache=False)

        if not result.signals:
            print(colorize("  无信号数据 / No signal data.", Colors.YELLOW))
            return 0

        print()
        print(render_channel_heatmap(result.signals))
        print()
        print(render_distribution(result.signals))

        return 0


# ============================================================
# 入口函数 / Entry Point Function
# ============================================================
def main(args: Optional[List[str]] = None) -> int:
    """
    CLI主入口 / CLI main entry point

    Args / 参数:
        args: 命令行参数 / Command line arguments

    Returns / 返回:
        退出码 / Exit code
    """
    cli = WaveSenseCLI()
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())
