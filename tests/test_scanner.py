"""
WaveSense-CLI - 扫描器测试 / Scanner Tests
=============================================

测试WiFi信号扫描引擎的解析功能和平台检测。
Test WiFi signal scanning engine parsing and platform detection.

使用mock替代真实系统命令调用。
Uses mock instead of real system command calls.
"""

import json
import os
import sys
import time
import unittest
from unittest.mock import patch, MagicMock
from io import StringIO

# 确保可以导入项目模块 / Ensure project modules can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wavesense_cli.scanner import WiFiScanner, ScanError
from wavesense_cli.models import WiFiSignal, ScanResult, SignalLevel, Platform


# ============================================================
# 模拟扫描数据 / Mock Scan Data
# ============================================================
NMCLI_OUTPUT = """MyHomeNetwork:AA:BB:CC:DD:EE:01:6:2437:85:WPA2:wlan0
OfficeWiFi:AA:BB:CC:DD:EE:02:11:2462:72:WPA2:wlan0
CafeFree:AA:BB:CC:DD:EE:03:1:2412:45:WPA2:wlan0
GuestNetwork:AA:BB:CC:DD:EE:04:36:5180:60:WPA2:wlan0
:00:00:00:00:00:00:3:2422:30::wlan0"""

IWLIST_OUTPUT = """wlan0     Scan completed :
          Cell 01 - Address: AA:BB:CC:DD:EE:01
                    ESSID:"MyHomeNetwork"
                    Protocol:IEEE 802.11bgn
                    Mode:Managed
                    Frequency:2.437 GHz (Channel 6)
                    Quality:70/100  Signal level:-55 dBm
                    Encryption key:on
                    IE: IEEE 802.11i
                    IE: WPA2 Version 1

          Cell 02 - Address: AA:BB:CC:DD:EE:02
                    ESSID:"OfficeWiFi"
                    Protocol:IEEE 802.11bgn
                    Mode:Managed
                    Frequency:2.462 GHz (Channel 11)
                    Quality:60/100  Signal level:-65 dBm
                    Encryption key:on
                    IE: WPA Version 2"""

AIRPORT_OUTPUT = """                            SSID                             BSSID             RSSI  CHANNEL  HT CC
  MyHomeNetwork              AA:BB:CC:DD:EE:01 -55  6       Y  US
  OfficeWiFi                 AA:BB:CC:DD:EE:02 -65  11      Y  US
  CafeFree                   AA:BB:CC:DD:EE:03 -45  1       Y  US"""

NETSH_OUTPUT = """Interface name : Wi-Fi
There are 3 networks currently visible.

SSID 1 : MyHomeNetwork
    Network type             : Infrastructure
    Authentication           : WPA2-Personal
    BSSID 1                  : aa:bb:cc:dd:ee:01
         Signal             : 75%
         Channel            : 6

SSID 2 : OfficeWiFi
    Network type             : Infrastructure
    Authentication           : WPA2-Personal
    BSSID 1                  : aa:bb:cc:dd:ee:02
         Signal             : 60%
         Channel            : 11"""


class TestNmcliParser(unittest.TestCase):
    """nmcli输出解析测试 / nmcli output parsing tests"""

    def setUp(self) -> None:
        """设置测试 / Setup test"""
        self.scanner = WiFiScanner()

    def test_parse_basic_output(self) -> None:
        """测试基本nmcli输出解析 / Test basic nmcli output parsing"""
        signals = self.scanner._parse_nmcli_output(NMCLI_OUTPUT)
        self.assertGreater(len(signals), 0)

        # 验证第一个信号 / Verify first signal
        first = signals[0]
        self.assertEqual(first.ssid, "MyHomeNetwork")
        self.assertEqual(first.bssid, "AA:BB:CC:DD:EE:01")
        self.assertEqual(first.channel, 6)
        self.assertEqual(first.security, "WPA2")

    def test_parse_hidden_ssid(self) -> None:
        """测试隐藏SSID解析 / Test hidden SSID parsing"""
        signals = self.scanner._parse_nmcli_output(NMCLI_OUTPUT)
        hidden = [s for s in signals if s.ssid == ""]
        self.assertTrue(len(hidden) > 0, "应检测到隐藏网络 / Should detect hidden network")

    def test_parse_rssi_range(self) -> None:
        """测试RSSI值范围 / Test RSSI value range"""
        signals = self.scanner._parse_nmcli_output(NMCLI_OUTPUT)
        for signal in signals:
            self.assertGreaterEqual(signal.rssi, -100)
            self.assertLessEqual(signal.rssi, 0)

    def test_parse_empty_output(self) -> None:
        """测试空输出处理 / Test empty output handling"""
        signals = self.scanner._parse_nmcli_output("")
        self.assertEqual(len(signals), 0)

    def test_parse_header_only(self) -> None:
        """测试仅标题行处理 / Test header-only handling"""
        signals = self.scanner._parse_nmcli_output("SSID:BSSID:CHAN:FREQ:SIGNAL:SECURITY:DEVICE")
        self.assertEqual(len(signals), 0)


class TestIwlistParser(unittest.TestCase):
    """iwlist输出解析测试 / iwlist output parsing tests"""

    def setUp(self) -> None:
        self.scanner = WiFiScanner()

    def test_parse_basic_output(self) -> None:
        """测试基本iwlist输出解析 / Test basic iwlist output parsing"""
        signals = self.scanner._parse_iwlist_output(IWLIST_OUTPUT)
        self.assertEqual(len(signals), 2)

        first = signals[0]
        self.assertEqual(first.ssid, "MyHomeNetwork")
        self.assertEqual(first.bssid, "AA:BB:CC:DD:EE:01")
        self.assertEqual(first.channel, 6)
        self.assertEqual(first.rssi, -55)
        self.assertEqual(first.security, "WPA2")

    def test_parse_frequency(self) -> None:
        """测试频率解析 / Test frequency parsing"""
        signals = self.scanner._parse_iwlist_output(IWLIST_OUTPUT)
        self.assertEqual(signals[0].frequency, 2437)
        self.assertEqual(signals[1].frequency, 2462)

    def test_parse_quality_format(self) -> None:
        """测试Quality格式解析 / Test Quality format parsing"""
        # 使用Quality格式而非dBm格式 / Use Quality format instead of dBm
        output = """Cell 01 - Address: AA:BB:CC:DD:EE:01
                    ESSID:"TestNet"
                    Quality:80/100  Signal level=-50 dBm
                    Channel:6"""
        signals = self.scanner._parse_iwlist_output(output)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].rssi, -50)


class TestAirportParser(unittest.TestCase):
    """airport输出解析测试 / airport output parsing tests"""

    def setUp(self) -> None:
        self.scanner = WiFiScanner()

    def test_parse_basic_output(self) -> None:
        """测试基本airport输出解析 / Test basic airport output parsing"""
        signals = self.scanner._parse_airport_output(AIRPORT_OUTPUT)
        self.assertEqual(len(signals), 3)

        first = signals[0]
        self.assertEqual(first.ssid, "MyHomeNetwork")
        self.assertEqual(first.bssid, "AA:BB:CC:DD:EE:01")
        self.assertEqual(first.rssi, -55)
        self.assertEqual(first.channel, 6)

    def test_parse_frequency_inference(self) -> None:
        """测试频率推断 / Test frequency inference"""
        signals = self.scanner._parse_airport_output(AIRPORT_OUTPUT)
        # Channel 6 -> 2437 MHz
        self.assertEqual(signals[0].frequency, 2437)
        # Channel 11 -> 2462 MHz
        self.assertEqual(signals[1].frequency, 2462)


class TestNetshParser(unittest.TestCase):
    """netsh输出解析测试 / netsh output parsing tests"""

    def setUp(self) -> None:
        self.scanner = WiFiScanner()

    def test_parse_basic_output(self) -> None:
        """测试基本netsh输出解析 / Test basic netsh output parsing"""
        signals = self.scanner._parse_netsh_output(NETSH_OUTPUT)
        self.assertEqual(len(signals), 2)

        first = signals[0]
        self.assertEqual(first.ssid, "MyHomeNetwork")
        self.assertEqual(first.bssid, "AA:BB:CC:DD:EE:01")
        self.assertEqual(first.channel, 6)
        self.assertEqual(first.security, "WPA2-Personal")

    def test_parse_signal_percentage(self) -> None:
        """测试信号百分比转换 / Test signal percentage conversion"""
        signals = self.scanner._parse_netsh_output(NETSH_OUTPUT)
        # 75% -> roughly -47 dBm
        self.assertGreater(signals[0].rssi, -60)
        self.assertLess(signals[0].rssi, -30)


class TestScannerMock(unittest.TestCase):
    """扫描器mock测试 / Scanner mock tests"""

    @patch("wavesense_cli.scanner.run_command")
    def test_scan_with_mock(self, mock_run: MagicMock) -> None:
        """测试mock扫描 / Test mock scan"""
        mock_run.return_value = (0, NMCLI_OUTPUT, "")

        scanner = WiFiScanner()
        # 强制平台为Linux / Force platform to Linux
        scanner._platform = Platform.LINUX

        result = scanner.scan()
        self.assertIsInstance(result, ScanResult)
        self.assertGreater(result.signal_count, 0)

    @patch("wavesense_cli.scanner.run_command")
    def test_scan_failure(self, mock_run: MagicMock) -> None:
        """测试扫描失败处理 / Test scan failure handling"""
        mock_run.return_value = (1, "", "Error: permission denied")

        scanner = WiFiScanner()
        scanner._platform = Platform.LINUX

        result = scanner.scan()
        self.assertEqual(result.signal_count, 0)
        self.assertIsNotNone(result.error)

    @patch("wavesense_cli.scanner.run_command")
    def test_scan_timeout(self, mock_run: MagicMock) -> None:
        """测试扫描超时处理 / Test scan timeout handling"""
        mock_run.return_value = (-1, "", "Command timed out")

        scanner = WiFiScanner()
        scanner._platform = Platform.LINUX

        result = scanner.scan()
        self.assertEqual(result.signal_count, 0)

    def test_cache_mechanism(self) -> None:
        """测试缓存机制 / Test cache mechanism"""
        scanner = WiFiScanner()
        scanner._cache_ttl = 60.0

        # 创建缓存结果 / Create cached result
        cached_result = ScanResult(
            signals=[WiFiSignal(ssid="Test", bssid="AA:BB:CC:DD:EE:FF", rssi=-50)],
        )
        scanner._cache = cached_result
        scanner._cache_time = time.time() + 1000000  # 未来时间 / Future time

        result = scanner.scan(use_cache=True)
        self.assertEqual(result.signal_count, 1)
        self.assertEqual(result.signals[0].ssid, "Test")

    def test_clear_cache(self) -> None:
        """测试缓存清除 / Test cache clearing"""
        scanner = WiFiScanner()
        scanner._cache = ScanResult()
        scanner._cache_time = 1000000

        scanner.clear_cache()
        self.assertIsNone(scanner.cache)


if __name__ == "__main__":
    unittest.main()
