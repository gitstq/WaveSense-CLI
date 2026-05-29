"""
WaveSense-CLI - 信号数据分析引擎 / Signal Data Analysis Engine
================================================================

提供WiFi信号数据的统计分析、异常检测、趋势分析和距离估算。
Provides statistical analysis, anomaly detection, trend analysis,
and distance estimation for WiFi signal data.

核心算法 / Core Algorithms:
    - Z-Score异常检测 / Z-Score anomaly detection
    - 线性回归趋势分析 / Linear regression trend analysis
    - FSPL距离估算 / FSPL distance estimation
    - 描述性统计 / Descriptive statistics
"""

from __future__ import annotations

import logging
import math
import time
from typing import Dict, List, Optional, Tuple

from .models import (
    AnalysisResult,
    Anomaly,
    ScanResult,
    SignalHistory,
    SignalRecord,
    SignalStatistics,
    TrendResult,
    WiFiSignal,
    classify_signal,
)
from .utils import estimate_distance_fspl, linear_regression, calculate_r_squared

logger = logging.getLogger("wavesense.analyzer")


# ============================================================
# 自定义异常 / Custom Exceptions
# ============================================================
class AnalysisError(Exception):
    """分析错误基类 / Base analysis error"""
    pass


class InsufficientDataError(AnalysisError):
    """数据不足错误 / Insufficient data error"""
    pass


# ============================================================
# 统计分析 / Statistical Analysis
# ============================================================
def calculate_statistics(signals: List[WiFiSignal]) -> SignalStatistics:
    """
    计算信号强度统计信息 / Calculate signal strength statistics
    ==============================================================
    对一组WiFi信号的RSSI值进行描述性统计分析。
    Perform descriptive statistical analysis on RSSI values of WiFi signals.

    Args / 参数:
        signals: WiFi信号列表 / List of WiFi signals

    Returns / 返回:
        SignalStatistics: 统计结果 / Statistics result
    """
    if not signals:
        return SignalStatistics()

    rssi_values = sorted([s.rssi for s in signals])
    n = len(rssi_values)

    # 均值 / Mean
    mean = sum(rssi_values) / n

    # 中位数 / Median
    if n % 2 == 0:
        median = (rssi_values[n // 2 - 1] + rssi_values[n // 2]) / 2
    else:
        median = rssi_values[n // 2]

    # 方差 / Variance (population)
    variance = sum((x - mean) ** 2 for x in rssi_values) / n if n > 0 else 0.0

    # 标准差 / Standard deviation
    std_dev = math.sqrt(variance)

    return SignalStatistics(
        mean=round(mean, 2),
        median=round(median, 2),
        std_dev=round(std_dev, 2),
        variance=round(variance, 2),
        min_val=float(min(rssi_values)),
        max_val=float(max(rssi_values)),
        count=n,
    )


def calculate_statistics_by_ssid(signals: List[WiFiSignal]) -> Dict[str, SignalStatistics]:
    """
    按SSID分组计算统计信息 / Calculate statistics grouped by SSID

    Args / 参数:
        signals: WiFi信号列表 / List of WiFi signals

    Returns / 返回:
        按SSID索引的统计字典 / Statistics dictionary indexed by SSID
    """
    groups: Dict[str, List[WiFiSignal]] = {}
    for s in signals:
        key = s.ssid if s.ssid else "(隐藏/Hidden)"
        if key not in groups:
            groups[key] = []
        groups[key].append(s)

    return {ssid: calculate_statistics(group) for ssid, group in groups.items()}


# ============================================================
# 异常检测 / Anomaly Detection
# ============================================================
def detect_anomalies(
    history: SignalHistory,
    threshold: float = 2.0,
) -> List[Anomaly]:
    """
    基于Z-Score的信号异常检测 / Z-Score based signal anomaly detection
    =====================================================================
    对每个BSSID的信号历史进行Z-Score分析，检测异常波动。
    Perform Z-Score analysis on signal history for each BSSID to detect abnormal fluctuations.

    Z-Score = (x - mean) / std_dev
    当 |Z-Score| > threshold 时判定为异常。
    An anomaly is detected when |Z-Score| > threshold.

    Args / 参数:
        history: 信号历史记录 / Signal history records
        threshold: Z-Score阈值 / Z-Score threshold (default: 2.0)

    Returns / 返回:
        异常列表 / List of anomalies
    """
    anomalies: List[Anomaly] = []

    for bssid in history.unique_bssids:
        records = history.get_by_bssid(bssid)
        if len(records) < 3:
            continue

        rssi_values = [r.rssi for r in records]
        n = len(rssi_values)
        mean = sum(rssi_values) / n
        variance = sum((x - mean) ** 2 for x in rssi_values) / n
        std_dev = math.sqrt(variance) if variance > 0 else 1.0

        for record in records:
            z_score = (record.rssi - mean) / std_dev
            if abs(z_score) > threshold:
                direction = "信号突然增强/Signal suddenly strengthened" if z_score < 0 else "信号突然减弱/Signal suddenly weakened"
                anomalies.append(Anomaly(
                    ssid=record.ssid,
                    bssid=record.bssid,
                    rssi=record.rssi,
                    z_score=round(z_score, 3),
                    timestamp=record.timestamp,
                    description=f"Z-Score={z_score:.2f}, {direction} (均值/Mean={mean:.1f} dBm)",
                ))

    logger.debug("异常检测完成 / Anomaly detection completed: %d anomalies found", len(anomalies))
    return anomalies


# ============================================================
# 趋势分析 / Trend Analysis
# ============================================================
def analyze_trend(
    history: SignalHistory,
    min_samples: int = 5,
) -> Dict[str, TrendResult]:
    """
    信号趋势分析 / Signal Trend Analysis
    =====================================
    对每个BSSID的信号历史进行线性回归分析，判断信号变化趋势。
    Perform linear regression analysis on signal history for each BSSID
    to determine signal change trends.

    Args / 参数:
        history: 信号历史记录 / Signal history records
        min_samples: 最小样本数 / Minimum sample count

    Returns / 返回:
        按BSSID索引的趋势结果 / Trend results indexed by BSSID
    """
    trends: Dict[str, TrendResult] = {}

    for bssid in history.unique_bssids:
        records = history.get_by_bssid(bssid)
        if len(records) < min_samples:
            continue

        # 按时间排序 / Sort by time
        sorted_records = sorted(records, key=lambda r: r.timestamp)

        # 构建时间序列 / Build time series
        # 使用相对时间（秒）作为x轴 / Use relative time (seconds) as x-axis
        base_time = sorted_records[0].timestamp
        x = [r.timestamp - base_time for r in sorted_records]
        y = [float(r.rssi) for r in sorted_records]

        # 线性回归 / Linear regression
        slope, intercept = linear_regression(x, y)

        # 计算R-squared / Calculate R-squared
        r_squared = calculate_r_squared(x, y)

        # 判断趋势方向 / Determine trend direction
        # slope单位: dBm/秒 / dBm per second
        # 将slope转换为dBm/分钟以便理解 / Convert slope to dBm/min for readability
        slope_per_min = slope * 60

        if abs(slope_per_min) < 0.5:
            direction = "stable"
        elif slope_per_min > 0:
            direction = "rising"
        else:
            direction = "falling"

        trends[bssid] = TrendResult(
            slope=round(slope, 6),
            intercept=round(intercept, 2),
            direction=direction,
            confidence=round(r_squared, 3),
        )

    logger.debug("趋势分析完成 / Trend analysis completed: %d BSSIDs analyzed", len(trends))
    return trends


# ============================================================
# 距离估算 / Distance Estimation
# ============================================================
def estimate_distance(rssi: int, frequency_mhz: int = 2412) -> float:
    """
    基于RSSI估算距离 / Estimate distance based on RSSI
    =====================================================
    使用自由空间路径损耗（FSPL）模型进行粗略距离估算。
    Use Free Space Path Loss (FSPL) model for rough distance estimation.

    注意：此估算受环境影响较大，仅供参考。
    Note: This estimate is heavily affected by environment, for reference only.

    Args / 参数:
        rssi: 信号强度（dBm）/ Signal strength in dBm
        frequency_mhz: 信号频率（MHz）/ Signal frequency in MHz

    Returns / 返回:
        估算距离（米）/ Estimated distance in meters
    """
    return estimate_distance_fspl(rssi, frequency_mhz)


def estimate_distances_for_signals(signals: List[WiFiSignal]) -> List[Tuple[WiFiSignal, float]]:
    """
    为所有信号估算距离 / Estimate distances for all signals

    Args / 参数:
        signals: WiFi信号列表 / List of WiFi signals

    Returns / 返回:
        (信号, 估算距离) 元组列表 / List of (signal, estimated distance) tuples
    """
    results: List[Tuple[WiFiSignal, float]] = []
    for signal in signals:
        freq = signal.frequency if signal.frequency > 0 else 2412
        distance = estimate_distance_fspl(signal.rssi, freq)
        results.append((signal, distance))
    return results


# ============================================================
# 信号分类 / Signal Classification
# ============================================================
def classify_signals(signals: List[WiFiSignal]) -> Dict[str, List[WiFiSignal]]:
    """
    按信号强度等级分类 / Classify by signal strength level

    Args / 参数:
        signals: WiFi信号列表 / List of WiFi signals

    Returns / 返回:
        按等级索引的信号字典 / Signal dictionary indexed by level
    """
    categories: Dict[str, List[WiFiSignal]] = {
        "excellent": [],
        "strong": [],
        "good": [],
        "weak": [],
        "very_weak": [],
    }

    for signal in signals:
        level = classify_signal(signal.rssi)
        categories[level.value].append(signal)

    return categories


def get_signal_summary(signals: List[WiFiSignal]) -> Dict[str, any]:
    """
    生成信号摘要 / Generate signal summary

    Args / 参数:
        signals: WiFi信号列表 / List of WiFi signals

    Returns / 返回:
        摘要字典 / Summary dictionary
    """
    if not signals:
        return {
            "total": 0,
            "strongest": None,
            "weakest": None,
            "average_rssi": 0,
            "categories": {},
        }

    stats = calculate_statistics(signals)
    categories = classify_signals(signals)

    strongest = max(signals, key=lambda s: s.rssi)
    weakest = min(signals, key=lambda s: s.rssi)

    return {
        "total": len(signals),
        "strongest": {
            "ssid": strongest.ssid or "(隐藏/Hidden)",
            "bssid": strongest.bssid,
            "rssi": strongest.rssi,
            "level": strongest.signal_level.value,
        },
        "weakest": {
            "ssid": weakest.ssid or "(隐藏/Hidden)",
            "bssid": weakest.bssid,
            "rssi": weakest.rssi,
            "level": weakest.signal_level.value,
        },
        "average_rssi": stats.mean,
        "statistics": stats.to_dict(),
        "categories": {k: len(v) for k, v in categories.items()},
    }


# ============================================================
# 综合分析 / Comprehensive Analysis
# ============================================================
def analyze_scan_result(result: ScanResult) -> AnalysisResult:
    """
    分析单次扫描结果 / Analyze a single scan result

    Args / 参数:
        result: 扫描结果 / Scan result

    Returns / 返回:
        AnalysisResult: 分析结果 / Analysis result
    """
    statistics = calculate_statistics(result.signals)
    summary = get_signal_summary(result.signals)

    return AnalysisResult(
        statistics=statistics,
        anomalies=[],
        trends={},
        analysis_time=time.time(),
    )


def analyze_history(history: SignalHistory) -> AnalysisResult:
    """
    分析信号历史数据 / Analyze signal history data
    ===============================================
    对历史数据进行全面的统计分析、异常检测和趋势分析。
    Perform comprehensive statistical analysis, anomaly detection,
    and trend analysis on historical data.

    Args / 参数:
        history: 信号历史记录 / Signal history records

    Returns / 返回:
        AnalysisResult: 完整分析结果 / Complete analysis result

    Raises / 异常:
        InsufficientDataError: 数据不足 / Insufficient data
    """
    if history.record_count < 3:
        raise InsufficientDataError(
            f"历史数据不足（至少需要3条记录，当前{history.record_count}条）/ "
            f"Insufficient history data (need at least 3 records, have {history.record_count})"
        )

    # 获取所有RSSI值用于统计 / Get all RSSI values for statistics
    all_rssi = [r.rssi for r in history.records]
    stats = SignalStatistics(
        mean=round(sum(all_rssi) / len(all_rssi), 2),
        median=sorted(all_rssi)[len(all_rssi) // 2],
        min_val=float(min(all_rssi)),
        max_val=float(max(all_rssi)),
        count=len(all_rssi),
    )
    variance = sum((x - stats.mean) ** 2 for x in all_rssi) / len(all_rssi)
    stats.variance = round(variance, 2)
    stats.std_dev = round(math.sqrt(variance), 2)

    # 异常检测 / Anomaly detection
    config_threshold = 2.0  # 默认阈值 / Default threshold
    anomalies = detect_anomalies(history, threshold=config_threshold)

    # 趋势分析 / Trend analysis
    trends = analyze_trend(history)

    return AnalysisResult(
        statistics=stats,
        anomalies=anomalies,
        trends=trends,
        analysis_time=time.time(),
    )


# ============================================================
# 信道分析 / Channel Analysis
# ============================================================
def analyze_channels(signals: List[WiFiSignal]) -> Dict[str, any]:
    """
    分析WiFi信道使用情况 / Analyze WiFi channel usage

    Args / 参数:
        signals: WiFi信号列表 / List of WiFi signals

    Returns / 返回:
        信道分析结果 / Channel analysis result
    """
    channel_usage: Dict[int, List[WiFiSignal]] = {}
    for signal in signals:
        ch = signal.channel
        if ch > 0:
            if ch not in channel_usage:
                channel_usage[ch] = []
            channel_usage[ch].append(signal)

    # 找出最拥挤的信道 / Find most crowded channels
    sorted_channels = sorted(channel_usage.items(), key=lambda x: len(x[1]), reverse=True)

    # 2.4GHz非重叠信道分析 / 2.4GHz non-overlapping channel analysis
    non_overlapping = {1: 0, 6: 0, 11: 0}
    for ch, sigs in channel_usage.items():
        if ch in non_overlapping:
            non_overlapping[ch] = len(sigs)
        # 检查重叠信道 / Check overlapping channels
        for preferred_ch in non_overlapping:
            if abs(ch - preferred_ch) <= 2 and ch != preferred_ch:
                non_overlapping[preferred_ch] += len(sigs)

    return {
        "total_channels_used": len(channel_usage),
        "channel_details": {
            str(ch): {
                "count": len(sigs),
                "avg_rssi": round(sum(s.rssi for s in sigs) / len(sigs), 1),
                "networks": [s.ssid or "(隐藏/Hidden)" for s in sigs],
            }
            for ch, sigs in sorted_channels
        },
        "most_crowded": sorted_channels[0][0] if sorted_channels else None,
        "recommended_channel": min(non_overlapping, key=non_overlapping.get) if non_overlapping else None,
        "non_overlapping_usage": non_overlapping,
    }
