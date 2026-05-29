"""
WaveSense-CLI - 导出器测试 / Exporter Tests
=============================================

测试JSON、CSV、Markdown导出功能。
Test JSON, CSV, Markdown export functionality.
"""

import csv
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wavesense_cli.exporter import (
    export_json,
    export_csv,
    export_markdown,
    export_report,
    export_to_string,
    ExportError,
    UnsupportedFormatError,
)
from wavesense_cli.models import (
    WiFiSignal,
    ScanResult,
    SignalHistory,
    SignalRecord,
)


# ============================================================
# 测试辅助 / Test Helpers
# ============================================================
def create_test_signals(count: int = 3) -> list:
    """创建测试信号 / Create test signals"""
    return [
        WiFiSignal(
            ssid=f"Network_{i}",
            bssid=f"AA:BB:CC:DD:EE:{i:02X}",
            rssi=-40 - i * 15,
            channel=1 + i * 5,
            frequency=2412 + i * 25,
            security="WPA2",
        )
        for i in range(count)
    ]


def create_test_result() -> ScanResult:
    """创建测试扫描结果 / Create test scan result"""
    return ScanResult(
        signals=create_test_signals(3),
        platform="linux",
        interface="wlan0",
    )


class TestExportJSON(unittest.TestCase):
    """JSON导出测试 / JSON export tests"""

    def test_export_scan_result(self) -> None:
        """测试导出扫描结果 / Test export scan result"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            filepath = f.name

        try:
            result = create_test_result()
            output_path = export_json(result, filepath)

            # 验证文件存在 / Verify file exists
            self.assertTrue(os.path.exists(output_path))

            # 验证内容 / Verify content
            with open(output_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertEqual(data["signal_count"], 3)
            self.assertEqual(len(data["signals"]), 3)
            self.assertEqual(data["signals"][0]["ssid"], "Network_0")
        finally:
            os.unlink(filepath)

    def test_export_dict(self) -> None:
        """测试导出字典 / Test export dict"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            filepath = f.name

        try:
            data = {"key": "value", "number": 42}
            output_path = export_json(data, filepath)

            with open(output_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            self.assertEqual(loaded["key"], "value")
        finally:
            os.unlink(filepath)

    def test_export_creates_directory(self) -> None:
        """测试自动创建目录 / Test auto-create directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "sub", "dir", "test.json")
            result = create_test_result()
            output_path = export_json(result, filepath)
            self.assertTrue(os.path.exists(output_path))


class TestExportCSV(unittest.TestCase):
    """CSV导出测试 / CSV export tests"""

    def test_export_scan_result(self) -> None:
        """测试导出扫描结果为CSV / Test export scan result as CSV"""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            filepath = f.name

        try:
            result = create_test_result()
            output_path = export_csv(result, filepath)

            # 验证文件 / Verify file
            with open(output_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0]["ssid"], "Network_0")
            self.assertIn("rssi", rows[0])
            self.assertIn("channel", rows[0])
        finally:
            os.unlink(filepath)

    def test_export_empty_signals(self) -> None:
        """测试导出空信号 / Test export empty signals"""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            filepath = f.name

        try:
            result = ScanResult(signals=[])
            output_path = export_csv(result, filepath)
            self.assertTrue(os.path.exists(output_path))
        finally:
            os.unlink(filepath)

    def test_export_with_custom_delimiter(self) -> None:
        """测试自定义分隔符 / Test custom delimiter"""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            filepath = f.name

        try:
            result = create_test_result()
            output_path = export_csv(result, filepath, delimiter=";")

            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn(";", content)
        finally:
            os.unlink(filepath)


class TestExportMarkdown(unittest.TestCase):
    """Markdown导出测试 / Markdown export tests"""

    def test_export_scan_result(self) -> None:
        """测试导出扫描结果为Markdown / Test export scan result as Markdown"""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            filepath = f.name

        try:
            result = create_test_result()
            output_path = export_markdown(result, filepath)

            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("# WaveSense-CLI", content)
            self.assertIn("Network_0", content)
            self.assertIn("## 概览", content)
            self.assertIn("## 信号列表", content)
        finally:
            os.unlink(filepath)

    def test_export_with_custom_title(self) -> None:
        """测试自定义标题 / Test custom title"""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            filepath = f.name

        try:
            result = create_test_result()
            output_path = export_markdown(result, filepath, title="自定义报告标题")
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("自定义报告标题", content)
        finally:
            os.unlink(filepath)

    def test_export_empty_result(self) -> None:
        """测试导出空结果 / Test export empty result"""
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False, mode="w") as f:
            filepath = f.name

        try:
            result = ScanResult(signals=[])
            output_path = export_markdown(result, filepath)
            self.assertTrue(os.path.exists(output_path))
        finally:
            os.unlink(filepath)


class TestExportReport(unittest.TestCase):
    """统一导出接口测试 / Unified export interface tests"""

    def test_export_json_format(self) -> None:
        """测试JSON格式导出 / Test JSON format export"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = create_test_result()
            output_path = export_report(result, format="json", output_dir=tmpdir)
            self.assertTrue(os.path.exists(output_path))
            self.assertTrue(output_path.endswith(".json"))

    def test_export_csv_format(self) -> None:
        """测试CSV格式导出 / Test CSV format export"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = create_test_result()
            output_path = export_report(result, format="csv", output_dir=tmpdir)
            self.assertTrue(os.path.exists(output_path))
            self.assertTrue(output_path.endswith(".csv"))

    def test_export_markdown_format(self) -> None:
        """测试Markdown格式导出 / Test Markdown format export"""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = create_test_result()
            output_path = export_report(result, format="markdown", output_dir=tmpdir)
            self.assertTrue(os.path.exists(output_path))
            self.assertTrue(output_path.endswith(".md"))

    def test_export_with_specific_filepath(self) -> None:
        """测试指定文件路径导出 / Test export with specific filepath"""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            filepath = f.name

        try:
            result = create_test_result()
            output_path = export_report(result, format="json", filepath=filepath)
            self.assertEqual(output_path, filepath)
        finally:
            os.unlink(filepath)

    def test_export_unsupported_format(self) -> None:
        """测试不支持的格式 / Test unsupported format"""
        result = create_test_result()
        with self.assertRaises(UnsupportedFormatError):
            export_report(result, format="xml")


class TestExportToString(unittest.TestCase):
    """字符串导出测试 / String export tests"""

    def test_json_string(self) -> None:
        """测试JSON字符串导出 / Test JSON string export"""
        result = create_test_result()
        output = export_to_string(result, "json")
        data = json.loads(output)
        self.assertEqual(data["signal_count"], 3)

    def test_csv_string(self) -> None:
        """测试CSV字符串导出 / Test CSV string export"""
        result = create_test_result()
        output = export_to_string(result, "csv")
        self.assertIn("SSID", output)
        self.assertIn("Network_0", output)


if __name__ == "__main__":
    unittest.main()
