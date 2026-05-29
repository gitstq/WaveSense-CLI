"""
WaveSense-CLI - CLI测试 / CLI Tests
=====================================

测试命令行接口的参数解析和命令分发。
Test CLI argument parsing and command dispatch.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wavesense_cli.cli import WaveSenseCLI, main


class TestCLIParsing(unittest.TestCase):
    """CLI参数解析测试 / CLI argument parsing tests"""

    def setUp(self) -> None:
        self.cli = WaveSenseCLI()

    def test_no_command(self) -> None:
        """测试无命令 / Test no command"""
        exit_code = self.cli.run([])
        self.assertEqual(exit_code, 0)

    def test_version(self) -> None:
        """测试版本参数 / Test version argument"""
        with self.assertRaises(SystemExit) as ctx:
            self.cli.run(["--version"])
        self.assertEqual(ctx.exception.code, 0)

    def test_scan_command(self) -> None:
        """测试scan命令解析 / Test scan command parsing"""
        parsed = self.cli._parser.parse_args(["scan"])
        self.assertEqual(parsed.command, "scan")

    def test_scan_with_interface(self) -> None:
        """测试scan命令带接口参数 / Test scan command with interface"""
        parsed = self.cli._parser.parse_args(["scan", "-i", "wlan0"])
        self.assertEqual(parsed.interface, "wlan0")

    def test_scan_with_json(self) -> None:
        """测试scan命令带JSON输出 / Test scan command with JSON output"""
        parsed = self.cli._parser.parse_args(["scan", "--json"])
        self.assertEqual(parsed.command, "scan")
        self.assertTrue(parsed.json)

    def test_scan_with_format(self) -> None:
        """测试scan命令带格式参数 / Test scan command with format"""
        parsed = self.cli._parser.parse_args(["scan", "-f", "json"])
        self.assertEqual(parsed.format, "json")

    def test_scan_with_output(self) -> None:
        """测试scan命令带输出路径 / Test scan command with output path"""
        parsed = self.cli._parser.parse_args(["scan", "-o", "result.json"])
        self.assertEqual(parsed.output, "result.json")

    def test_monitor_command(self) -> None:
        """测试monitor命令解析 / Test monitor command parsing"""
        parsed = self.cli._parser.parse_args(["monitor", "-i", "3", "-n", "5"])
        self.assertEqual(parsed.command, "monitor")
        self.assertEqual(parsed.interval, 3.0)
        self.assertEqual(parsed.count, 5)

    def test_dashboard_command(self) -> None:
        """测试dashboard命令解析 / Test dashboard command parsing"""
        parsed = self.cli._parser.parse_args(["dashboard", "--simple"])
        self.assertEqual(parsed.command, "dashboard")
        self.assertTrue(parsed.simple)

    def test_analyze_command(self) -> None:
        """测试analyze命令解析 / Test analyze command parsing"""
        parsed = self.cli._parser.parse_args(["analyze", "--threshold", "3.0"])
        self.assertEqual(parsed.command, "analyze")
        self.assertEqual(parsed.threshold, 3.0)

    def test_report_command(self) -> None:
        """测试report命令解析 / Test report command parsing"""
        parsed = self.cli._parser.parse_args(["report", "-f", "markdown", "-o", "report.md"])
        self.assertEqual(parsed.command, "report")
        self.assertEqual(parsed.format, "markdown")
        self.assertEqual(parsed.output, "report.md")

    def test_heatmap_command(self) -> None:
        """测试heatmap命令解析 / Test heatmap command parsing"""
        parsed = self.cli._parser.parse_args(["heatmap"])
        self.assertEqual(parsed.command, "heatmap")

    def test_verbose_flag(self) -> None:
        """测试verbose标志 / Test verbose flag"""
        parsed = self.cli._parser.parse_args(["-v", "scan"])
        self.assertTrue(parsed.verbose)


class TestCLIExecution(unittest.TestCase):
    """CLI命令执行测试 / CLI command execution tests"""

    def setUp(self) -> None:
        self.cli = WaveSenseCLI()

    @patch("wavesense_cli.cli.WiFiScanner")
    def test_scan_with_mock(self, mock_scanner_class: MagicMock) -> None:
        """测试mock扫描执行 / Test mock scan execution"""
        mock_scanner = MagicMock()
        mock_result = MagicMock()
        mock_result.signals = []
        mock_result.signal_count = 0
        mock_result.scan_time = 0
        mock_result.scan_duration = 0.5
        mock_result.to_json.return_value = '{"signals": []}'
        mock_scanner.scan.return_value = mock_result
        mock_scanner_class.return_value = mock_scanner

        exit_code = self.cli.run(["scan"])
        self.assertEqual(exit_code, 0)
        mock_scanner.scan.assert_called_once()

    @patch("wavesense_cli.cli.WiFiScanner")
    def test_scan_json_output(self, mock_scanner_class: MagicMock) -> None:
        """测试JSON输出 / Test JSON output"""
        mock_scanner = MagicMock()
        mock_result = MagicMock()
        mock_result.signals = []
        mock_result.signal_count = 0
        mock_result.to_json.return_value = '{"signal_count": 0, "signals": []}'
        mock_scanner.scan.return_value = mock_result
        mock_scanner_class.return_value = mock_scanner

        with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
            exit_code = self.cli.run(["scan", "--json"])
            output = mock_stdout.getvalue()
            self.assertIn("signal_count", output)

    @patch("wavesense_cli.cli.WiFiScanner")
    def test_scan_with_export(self, mock_scanner_class: MagicMock) -> None:
        """测试带导出的扫描 / Test scan with export"""
        mock_scanner = MagicMock()
        mock_result = MagicMock()
        mock_result.signals = [MagicMock()]
        mock_result.signal_count = 1
        mock_scanner.scan.return_value = mock_result
        mock_scanner_class.return_value = mock_scanner

        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test.json")
            with patch("wavesense_cli.cli.export_report") as mock_export:
                mock_export.return_value = filepath
                exit_code = self.cli.run(["scan", "-o", filepath])
                self.assertEqual(exit_code, 0)

    @patch("wavesense_cli.cli.WiFiScanner")
    def test_heatmap_with_mock(self, mock_scanner_class: MagicMock) -> None:
        """测试热力图命令 / Test heatmap command"""
        mock_scanner = MagicMock()
        mock_result = MagicMock()
        mock_result.signals = []
        mock_scanner.scan.return_value = mock_result
        mock_scanner_class.return_value = mock_scanner

        exit_code = self.cli.run(["heatmap"])
        self.assertEqual(exit_code, 0)


class TestMainFunction(unittest.TestCase):
    """main函数测试 / main function tests"""

    def test_main_no_args(self) -> None:
        """测试无参数main / Test main with no args"""
        with patch("sys.argv", ["wavesense"]):
            exit_code = main([])
            self.assertEqual(exit_code, 0)

    def test_main_help(self) -> None:
        """测试帮助 / Test help"""
        with patch("sys.argv", ["wavesense", "--help"]):
            with self.assertRaises(SystemExit) as ctx:
                main(["--help"])
            self.assertEqual(ctx.exception.code, 0)


# 需要导入tempfile / Need to import tempfile
import tempfile

if __name__ == "__main__":
    unittest.main()
