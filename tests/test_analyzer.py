"""
WaveSense-CLI - 分析器测试 / Analyzer Tests
=============================================

测试信号数据分析引擎的统计、异常检测和趋势分析功能。
Test signal data analysis engine statistics, anomaly detection, and trend analysis.
"""

import os
import sys
import math
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wavesense_cli.analyzer import (
    calculate_statistics,
    detect_anomalies,
    analyze_trend,
    estimate_distance,
    classify_signals,
    get_signal_summary,
    analyze_scan_result,
    analyze_channels,
    InsufficientDataError,
)
from wavesense_cli.models import (
    WiFiSignal,
    ScanResult,
    SignalHistory,
    SignalRecord,
    SignalStatistics,
    SignalLevel,
    classify_signal,
)


# ============================================================
# 测试辅助 / Test Helpers
# ============================================================
def create_test_signals(count: int = 10) -> list:
    """创建测试信号列表 / Create test signal list"""
    signals = []
    for i in range(count):
        signals.append(WiFiSignal(
            ssid=f"Network_{i}",
            bssid=f"AA:BB:CC:DD:EE:{i:02X}",
            rssi=-30 - i * 5,  # -30, -35, -40, ..., -75
            channel=1 + i,
            frequency=2412 + i * 5,
            security="WPA2",
        ))
    return signals


def create_test_history(bssid_count: int = 3, records_per_bssid: int = 10) -> SignalHistory:
    """创建测试历史数据 / Create test history data"""
    history = SignalHistory()
    base_time = time.time() - 100

    for b in range(bssid_count):
        bssid = f"AA:BB:CC:DD:EE:{b:02X}"
        ssid = f"Network_{b}"
        base_rssi = -50 - b * 10

        for i in range(records_per_bssid):
            # 添加一些正常波动 / Add some normal fluctuation
            rssi = base_rssi + (i % 3 - 1) * 2
            history.add_record(SignalRecord(
                ssid=ssid,
                bssid=bssid,
                rssi=rssi,
                timestamp=base_time + i * 5,
            ))

    return history


class TestClassifySignal(unittest.TestCase):
    """信号分类测试 / Signal classification tests"""

    def test_excellent(self) -> None:
        self.assertEqual(classify_signal(-30), SignalLevel.EXCELLENT)
        self.assertEqual(classify_signal(-45), SignalLevel.EXCELLENT)
        self.assertEqual(classify_signal(-50), SignalLevel.EXCELLENT)

    def test_strong(self) -> None:
        self.assertEqual(classify_signal(-51), SignalLevel.STRONG)
        self.assertEqual(classify_signal(-55), SignalLevel.STRONG)
        self.assertEqual(classify_signal(-60), SignalLevel.STRONG)

    def test_good(self) -> None:
        self.assertEqual(classify_signal(-61), SignalLevel.GOOD)
        self.assertEqual(classify_signal(-65), SignalLevel.GOOD)
        self.assertEqual(classify_signal(-70), SignalLevel.GOOD)

    def test_weak(self) -> None:
        self.assertEqual(classify_signal(-71), SignalLevel.WEAK)
        self.assertEqual(classify_signal(-75), SignalLevel.WEAK)
        self.assertEqual(classify_signal(-80), SignalLevel.WEAK)

    def test_very_weak(self) -> None:
        self.assertEqual(classify_signal(-81), SignalLevel.VERY_WEAK)
        self.assertEqual(classify_signal(-90), SignalLevel.VERY_WEAK)
        self.assertEqual(classify_signal(-100), SignalLevel.VERY_WEAK)


class TestCalculateStatistics(unittest.TestCase):
    """统计分析测试 / Statistical analysis tests"""

    def test_basic_statistics(self) -> None:
        signals = create_test_signals(10)
        stats = calculate_statistics(signals)

        self.assertEqual(stats.count, 10)
        self.assertEqual(stats.min_val, -75.0)
        self.assertEqual(stats.max_val, -30.0)
        self.assertAlmostEqual(stats.mean, -52.5, places=1)

    def test_empty_signals(self) -> None:
        stats = calculate_statistics([])
        self.assertEqual(stats.count, 0)
        self.assertEqual(stats.mean, 0.0)

    def test_single_signal(self) -> None:
        signals = [WiFiSignal(ssid="Test", bssid="AA:BB:CC:DD:EE:FF", rssi=-60)]
        stats = calculate_statistics(signals)
        self.assertEqual(stats.count, 1)
        self.assertEqual(stats.mean, -60.0)
        self.assertEqual(stats.std_dev, 0.0)

    def test_uniform_signals(self) -> None:
        """测试所有信号相同的情况 / Test all signals are the same"""
        signals = [WiFiSignal(ssid="Test", bssid=f"AA:BB:CC:DD:EE:{i:02X}", rssi=-60) for i in range(5)]
        stats = calculate_statistics(signals)
        self.assertEqual(stats.std_dev, 0.0)
        self.assertEqual(stats.variance, 0.0)

    def test_median_odd(self) -> None:
        signals = [WiFiSignal(ssid=f"N{i}", bssid=f"AA:BB:CC:DD:EE:{i:02X}", rssi=-50 - i * 10) for i in range(5)]
        stats = calculate_statistics(signals)
        self.assertEqual(stats.median, -70.0)  # 中间值 / Middle value

    def test_median_even(self) -> None:
        signals = [WiFiSignal(ssid=f"N{i}", bssid=f"AA:BB:CC:DD:EE:{i:02X}", rssi=-50 - i * 10) for i in range(4)]
        stats = calculate_statistics(signals)
        self.assertEqual(stats.median, -65.0)  # (-60 + -70) / 2


class TestDetectAnomalies(unittest.TestCase):
    """异常检测测试 / Anomaly detection tests"""

    def test_no_anomalies(self) -> None:
        """测试无异常情况 / Test no anomaly case"""
        history = create_test_history(bssid_count=2, records_per_bssid=10)
        anomalies = detect_anomalies(history, threshold=3.0)
        # 正常波动不应触发异常 / Normal fluctuation should not trigger anomaly
        self.assertEqual(len(anomalies), 0)

    def test_with_anomaly(self) -> None:
        """测试有异常情况 / Test with anomaly case"""
        history = SignalHistory()
        base_time = time.time()

        # 正常数据 / Normal data
        for i in range(10):
            history.add_record(SignalRecord(
                ssid="TestNet", bssid="AA:BB:CC:DD:EE:01",
                rssi=-60, timestamp=base_time + i,
            ))

        # 添加异常数据 / Add anomalous data
        history.add_record(SignalRecord(
            ssid="TestNet", bssid="AA:BB:CC:DD:EE:01",
            rssi=-30, timestamp=base_time + 10,  # 突然增强 / Sudden strengthening
        ))

        anomalies = detect_anomalies(history, threshold=2.0)
        self.assertGreater(len(anomalies), 0)

    def test_insufficient_data(self) -> None:
        """测试数据不足 / Test insufficient data"""
        history = SignalHistory()
        history.add_record(SignalRecord(ssid="T", bssid="AA:BB:CC:DD:EE:01", rssi=-60))
        anomalies = detect_anomalies(history)
        self.assertEqual(len(anomalies), 0)


class TestAnalyzeTrend(unittest.TestCase):
    """趋势分析测试 / Trend analysis tests"""

    def test_rising_trend(self) -> None:
        """测试上升趋势 / Test rising trend"""
        history = SignalHistory()
        base_time = time.time()

        for i in range(10):
            history.add_record(SignalRecord(
                ssid="TestNet", bssid="AA:BB:CC:DD:EE:01",
                rssi=-80 + i * 3,  # 逐渐增强 / Gradually strengthening
                timestamp=base_time + i * 5,
            ))

        trends = analyze_trend(history, min_samples=5)
        self.assertIn("AA:BB:CC:DD:EE:01", trends)
        self.assertEqual(trends["AA:BB:CC:DD:EE:01"].direction, "rising")

    def test_falling_trend(self) -> None:
        """测试下降趋势 / Test falling trend"""
        history = SignalHistory()
        base_time = time.time()

        for i in range(10):
            history.add_record(SignalRecord(
                ssid="TestNet", bssid="AA:BB:CC:DD:EE:02",
                rssi=-40 - i * 3,  # 逐渐减弱 / Gradually weakening
                timestamp=base_time + i * 5,
            ))

        trends = analyze_trend(history, min_samples=5)
        self.assertIn("AA:BB:CC:DD:EE:02", trends)
        self.assertEqual(trends["AA:BB:CC:DD:EE:02"].direction, "falling")

    def test_stable_trend(self) -> None:
        """测试稳定趋势 / Test stable trend"""
        history = SignalHistory()
        base_time = time.time()

        for i in range(10):
            history.add_record(SignalRecord(
                ssid="TestNet", bssid="AA:BB:CC:DD:EE:03",
                rssi=-60 + (i % 3 - 1),  # 小幅波动 / Small fluctuation
                timestamp=base_time + i * 5,
            ))

        trends = analyze_trend(history, min_samples=5)
        self.assertIn("AA:BB:CC:DD:EE:03", trends)
        self.assertEqual(trends["AA:BB:CC:DD:EE:03"].direction, "stable")


class TestEstimateDistance(unittest.TestCase):
    """距离估算测试 / Distance estimation tests"""

    def test_strong_signal(self) -> None:
        """测试强信号距离估算 / Test strong signal distance estimation"""
        distance = estimate_distance(-30, 2412)
        self.assertLess(distance, 5.0)  # 近距离 / Close range

    def test_weak_signal(self) -> None:
        """测试弱信号距离估算 / Test weak signal distance estimation"""
        distance = estimate_distance(-80, 2412)
        self.assertGreater(distance, 10.0)  # 远距离 / Far range

    def test_5ghz_vs_24ghz(self) -> None:
        """测试5GHz与2.4GHz差异 / Test 5GHz vs 2.4GHz difference"""
        dist_24 = estimate_distance(-60, 2412)
        dist_5 = estimate_distance(-60, 5180)
        # 5GHz参考RSSI更低（-47 vs -40），相同RSSI下5GHz估算距离更远
        # 5GHz reference RSSI is lower (-47 vs -40), same RSSI gives larger 5GHz distance
        self.assertNotEqual(dist_5, dist_24)


class TestClassifySignals(unittest.TestCase):
    """信号分类测试 / Signal classification tests"""

    def test_classify_all_levels(self) -> None:
        signals = [
            WiFiSignal(ssid="E", bssid="AA:BB:CC:DD:EE:01", rssi=-40),
            WiFiSignal(ssid="S", bssid="AA:BB:CC:DD:EE:02", rssi=-55),
            WiFiSignal(ssid="G", bssid="AA:BB:CC:DD:EE:03", rssi=-65),
            WiFiSignal(ssid="W", bssid="AA:BB:CC:DD:EE:04", rssi=-75),
            WiFiSignal(ssid="V", bssid="AA:BB:CC:DD:EE:05", rssi=-85),
        ]
        categories = classify_signals(signals)

        self.assertEqual(len(categories["excellent"]), 1)
        self.assertEqual(len(categories["strong"]), 1)
        self.assertEqual(len(categories["good"]), 1)
        self.assertEqual(len(categories["weak"]), 1)
        self.assertEqual(len(categories["very_weak"]), 1)


class TestGetSignalSummary(unittest.TestCase):
    """信号摘要测试 / Signal summary tests"""

    def test_summary_with_signals(self) -> None:
        signals = create_test_signals(5)
        summary = get_signal_summary(signals)

        self.assertEqual(summary["total"], 5)
        self.assertIsNotNone(summary["strongest"])
        self.assertIsNotNone(summary["weakest"])
        self.assertEqual(summary["strongest"]["rssi"], -30)
        self.assertEqual(summary["weakest"]["rssi"], -50)

    def test_summary_empty(self) -> None:
        summary = get_signal_summary([])
        self.assertEqual(summary["total"], 0)
        self.assertIsNone(summary["strongest"])


class TestAnalyzeScanResult(unittest.TestCase):
    """扫描结果分析测试 / Scan result analysis tests"""

    def test_analyze_with_signals(self) -> None:
        signals = create_test_signals(5)
        result = ScanResult(signals=signals)
        analysis = analyze_scan_result(result)

        self.assertIsNotNone(analysis.statistics)
        self.assertEqual(analysis.statistics.count, 5)

    def test_analyze_empty(self) -> None:
        result = ScanResult(signals=[])
        analysis = analyze_scan_result(result)
        self.assertIsNotNone(analysis)


class TestAnalyzeChannels(unittest.TestCase):
    """信道分析测试 / Channel analysis tests"""

    def test_channel_analysis(self) -> None:
        signals = [
            WiFiSignal(ssid="N1", bssid="AA:BB:CC:DD:EE:01", rssi=-50, channel=1),
            WiFiSignal(ssid="N2", bssid="AA:BB:CC:DD:EE:02", rssi=-55, channel=6),
            WiFiSignal(ssid="N3", bssid="AA:BB:CC:DD:EE:03", rssi=-60, channel=6),
            WiFiSignal(ssid="N4", bssid="AA:BB:CC:DD:EE:04", rssi=-65, channel=11),
        ]
        result = analyze_channels(signals)

        self.assertEqual(result["total_channels_used"], 3)
        self.assertEqual(result["most_crowded"], 6)  # Ch6有2个 / Ch6 has 2
        self.assertIsNotNone(result["recommended_channel"])

    def test_empty_channels(self) -> None:
        result = analyze_channels([])
        self.assertEqual(result["total_channels_used"], 0)


if __name__ == "__main__":
    unittest.main()
