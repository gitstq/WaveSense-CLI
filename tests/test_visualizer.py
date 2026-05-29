"""
WaveSense-CLI - 可视化测试 / Visualizer Tests
==============================================

测试ASCII热力图、信号条形图、折线图等可视化渲染功能。
Test ASCII heatmap, signal bar chart, line chart visualization rendering.
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wavesense_cli.visualizer import (
    render_signal_bar,
    render_signal_bars,
    render_heatmap,
    render_channel_heatmap,
    render_signal_chart,
    render_dashboard_summary,
    render_distribution,
)
from wavesense_cli.models import (
    WiFiSignal,
    ScanResult,
    SignalHistory,
    SignalRecord,
    AnalysisResult,
    SignalStatistics,
)


# ============================================================
# 测试辅助 / Test Helpers
# ============================================================
def create_test_signals(count: int = 5) -> list:
    """创建测试信号 / Create test signals"""
    return [
        WiFiSignal(
            ssid=f"Network_{i}",
            bssid=f"AA:BB:CC:DD:EE:{i:02X}",
            rssi=-30 - i * 10,
            channel=(i % 3) * 5 + 1,
            frequency=2412 + (i % 3) * 25,
            security="WPA2",
        )
        for i in range(count)
    ]


def create_test_history() -> SignalHistory:
    """创建测试历史 / Create test history"""
    import time
    history = SignalHistory()
    base_time = time.time() - 50
    for i in range(20):
        history.add_record(SignalRecord(
            ssid="TestNet",
            bssid="AA:BB:CC:DD:EE:01",
            rssi=-60 + (i % 5) * 3,
            timestamp=base_time + i * 2.5,
        ))
    return history


class TestRenderSignalBar(unittest.TestCase):
    """信号条形图测试 / Signal bar chart tests"""

    def test_strong_signal(self) -> None:
        """测试强信号条形图 / Test strong signal bar"""
        bar = render_signal_bar(-30, width=20)
        self.assertIn("█", bar)
        self.assertIn("-30", bar)

    def test_weak_signal(self) -> None:
        """测试弱信号条形图 / Test weak signal bar"""
        bar = render_signal_bar(-90, width=20)
        self.assertIn("░", bar)
        self.assertIn("-90", bar)

    def test_without_label(self) -> None:
        """测试无标签模式 / Test no-label mode"""
        bar = render_signal_bar(-50, width=10, show_label=False)
        self.assertIn("[", bar)
        self.assertIn("]", bar)

    def test_zero_width(self) -> None:
        """测试零宽度 / Test zero width"""
        bar = render_signal_bar(-50, width=0, show_label=False)
        self.assertIn("[]", bar)


class TestRenderSignalBars(unittest.TestCase):
    """多信号条形图测试 / Multi-signal bar chart tests"""

    def test_multiple_signals(self) -> None:
        """测试多信号渲染 / Test multiple signals rendering"""
        signals = create_test_signals(5)
        output = render_signal_bars(signals, width=20)
        self.assertIn("Network_0", output)
        self.assertIn("Network_4", output)

    def test_empty_signals(self) -> None:
        """测试空信号 / Test empty signals"""
        output = render_signal_bars([])
        self.assertIn("无信号", output)

    def test_hidden_ssid(self) -> None:
        """测试隐藏SSID / Test hidden SSID"""
        signals = [WiFiSignal(ssid="", bssid="AA:BB:CC:DD:EE:FF", rssi=-50)]
        output = render_signal_bars(signals)
        self.assertIn("隐藏", output)


class TestRenderHeatmap(unittest.TestCase):
    """热力图测试 / Heatmap tests"""

    def test_basic_heatmap(self) -> None:
        """测试基本热力图 / Test basic heatmap"""
        data = [
            [0.0, 0.2, 0.4, 0.6, 0.8, 1.0],
            [0.1, 0.3, 0.5, 0.7, 0.9, 0.95],
        ]
        output = render_heatmap(data, width=30, height=5, use_color=False)
        self.assertIn("▁", output)
        self.assertIn("█", output)

    def test_empty_data(self) -> None:
        """测试空数据 / Test empty data"""
        output = render_heatmap([], width=30, height=5)
        self.assertIn("无数据", output)

    def test_single_value(self) -> None:
        """测试单值数据 / Test single value data"""
        data = [[0.5]]
        output = render_heatmap(data, width=10, height=5, use_color=False)
        self.assertIsNotNone(output)

    def test_with_title(self) -> None:
        """测试带标题热力图 / Test heatmap with title"""
        data = [[0.5, 0.7], [0.3, 0.9]]
        output = render_heatmap(data, title="测试热力图")
        self.assertIn("测试热力图", output)


class TestRenderChannelHeatmap(unittest.TestCase):
    """信道热力图测试 / Channel heatmap tests"""

    def test_channel_heatmap(self) -> None:
        """测试信道热力图 / Test channel heatmap"""
        signals = [
            WiFiSignal(ssid="N1", bssid="AA:BB:CC:DD:EE:01", rssi=-50, channel=1),
            WiFiSignal(ssid="N2", bssid="AA:BB:CC:DD:EE:02", rssi=-55, channel=6),
            WiFiSignal(ssid="N3", bssid="AA:BB:CC:DD:EE:03", rssi=-60, channel=6),
            WiFiSignal(ssid="N4", bssid="AA:BB:CC:DD:EE:04", rssi=-65, channel=11),
        ]
        output = render_channel_heatmap(signals)
        self.assertIn("2.4GHz", output)
        self.assertIn("Ch", output)

    def test_empty_signals(self) -> None:
        """测试空信号信道图 / Test empty signal channel map"""
        output = render_channel_heatmap([])
        self.assertIn("无信号", output)

    def test_5ghz_channels(self) -> None:
        """测试5GHz信道 / Test 5GHz channels"""
        signals = [
            WiFiSignal(ssid="N5", bssid="AA:BB:CC:DD:EE:05", rssi=-50, channel=36),
            WiFiSignal(ssid="N6", bssid="AA:BB:CC:DD:EE:06", rssi=-55, channel=149),
        ]
        output = render_channel_heatmap(signals)
        self.assertIn("5GHz", output)


class TestRenderSignalChart(unittest.TestCase):
    """信号折线图测试 / Signal line chart tests"""

    def test_basic_chart(self) -> None:
        """测试基本折线图 / Test basic line chart"""
        history = create_test_history()
        output = render_signal_chart(history, width=50, height=10)
        self.assertIsNotNone(output)
        self.assertIn("●", output)

    def test_empty_history(self) -> None:
        """测试空历史折线图 / Test empty history chart"""
        history = SignalHistory()
        output = render_signal_chart(history)
        self.assertIn("无历史", output)

    def test_specific_bssid(self) -> None:
        """测试指定BSSID折线图 / Test specific BSSID chart"""
        history = create_test_history()
        output = render_signal_chart(history, bssid="AA:BB:CC:DD:EE:01")
        self.assertIn("TestNet", output)

    def test_nonexistent_bssid(self) -> None:
        """测试不存在BSSID / Test nonexistent BSSID"""
        history = create_test_history()
        output = render_signal_chart(history, bssid="AA:BB:CC:DD:EE:FF")
        self.assertIn("无匹配", output)


class TestRenderDashboardSummary(unittest.TestCase):
    """仪表盘摘要测试 / Dashboard summary tests"""

    def test_basic_summary(self) -> None:
        """测试基本摘要 / Test basic summary"""
        signals = create_test_signals(3)
        result = ScanResult(signals=signals, platform="linux")
        output = render_dashboard_summary(result)
        self.assertIn("WaveSense-CLI", output)
        self.assertIn("Network_0", output)

    def test_with_analysis(self) -> None:
        """测试带分析的摘要 / Test summary with analysis"""
        signals = create_test_signals(3)
        result = ScanResult(signals=signals)
        stats = SignalStatistics(mean=-50.0, count=3, min_val=-50.0, max_val=-30.0)
        analysis = AnalysisResult(statistics=stats)
        output = render_dashboard_summary(result, analysis)
        self.assertIn("统计", output)

    def test_empty_result(self) -> None:
        """测试空结果摘要 / Test empty result summary"""
        result = ScanResult(signals=[])
        output = render_dashboard_summary(result)
        self.assertIn("WaveSense-CLI", output)


class TestRenderDistribution(unittest.TestCase):
    """信号分布图测试 / Signal distribution tests"""

    def test_distribution(self) -> None:
        """测试信号分布 / Test signal distribution"""
        signals = [
            WiFiSignal(ssid="N1", bssid="AA:BB:CC:DD:EE:01", rssi=-40),
            WiFiSignal(ssid="N2", bssid="AA:BB:CC:DD:EE:02", rssi=-55),
            WiFiSignal(ssid="N3", bssid="AA:BB:CC:DD:EE:03", rssi=-65),
            WiFiSignal(ssid="N4", bssid="AA:BB:CC:DD:EE:04", rssi=-75),
            WiFiSignal(ssid="N5", bssid="AA:BB:CC:DD:EE:05", rssi=-85),
        ]
        output = render_distribution(signals)
        self.assertIn("极强", output)
        self.assertIn("极弱", output)
        self.assertIn("总计", output)

    def test_empty_distribution(self) -> None:
        """测试空分布 / Test empty distribution"""
        output = render_distribution([])
        self.assertIn("无数据", output)


if __name__ == "__main__":
    unittest.main()
