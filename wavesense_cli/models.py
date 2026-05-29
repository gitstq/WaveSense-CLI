"""
WaveSense-CLI - 数据模型定义 / Data Model Definitions
=======================================================

定义所有核心数据结构，使用 dataclass 实现类型安全的数据模型。
Define all core data structures using dataclass for type-safe data models.

包含：WiFi信号、扫描结果、分析结果、信号历史记录
Contains: WiFi signal, scan result, analysis result, signal history
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import List, Dict, Optional, Any


class SignalLevel(Enum):
    """信号强度等级枚举 / Signal strength level enumeration"""
    EXCELLENT = "excellent"   # 极强 / Excellent  (-30 ~ -50 dBm)
    STRONG = "strong"         # 强 / Strong      (-50 ~ -60 dBm)
    GOOD = "good"             # 中 / Good        (-60 ~ -70 dBm)
    WEAK = "weak"             # 弱 / Weak        (-70 ~ -80 dBm)
    VERY_WEAK = "very_weak"   # 极弱 / Very Weak  (< -80 dBm)
    UNKNOWN = "unknown"      # 未知 / Unknown


class Platform(Enum):
    """操作系统平台枚举 / Operating system platform enumeration"""
    LINUX = "linux"
    MACOS = "macos"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


@dataclass
class WiFiSignal:
    """
    WiFi信号数据模型 / WiFi Signal Data Model
    ==========================================
    表示单个WiFi接入点的信号信息。
    Represents signal information for a single WiFi access point.

    Attributes / 属性:
        ssid: 网络名称 / Network name (SSID)
        bssid: MAC地址 / MAC address (BSSID)
        rssi: 信号强度（dBm）/ Signal strength in dBm (typically -100 to 0)
        channel: 信道号 / Channel number
        frequency: 频率（MHz）/ Frequency in MHz
        security: 加密类型 / Encryption type
        signal_level: 信号等级 / Signal level classification
        timestamp: 扫描时间戳 / Scan timestamp (Unix epoch)
        interface: 网络接口 / Network interface name
    """
    ssid: str = ""
    bssid: str = ""
    rssi: int = -100
    channel: int = 0
    frequency: int = 0
    security: str = ""
    signal_level: SignalLevel = SignalLevel.UNKNOWN
    timestamp: float = field(default_factory=time.time)
    interface: str = ""

    def __post_init__(self) -> None:
        """初始化后自动分类信号等级 / Auto-classify signal level after initialization"""
        if self.signal_level == SignalLevel.UNKNOWN:
            self.signal_level = classify_signal(self.rssi)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        data = asdict(self)
        data["signal_level"] = self.signal_level.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WiFiSignal":
        """从字典创建 / Create from dictionary"""
        if "signal_level" in data and isinstance(data["signal_level"], str):
            data["signal_level"] = SignalLevel(data["signal_level"])
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def __str__(self) -> str:
        """格式化字符串输出 / Formatted string output"""
        ssid_display = self.ssid if self.ssid else "(隐藏网络/Hidden)"
        return (
            f"{ssid_display:<32} {self.bssid:>17}  "
            f"RSSI: {self.rssi:>4} dBm  "
            f"Ch: {self.channel:>3}  "
            f"[{self.signal_level.value:>10}]"
        )


@dataclass
class ScanResult:
    """
    扫描结果数据模型 / Scan Result Data Model
    ==========================================
    表示一次WiFi扫描的完整结果。
    Represents the complete result of a WiFi scan.

    Attributes / 属性:
        signals: 发现的信号列表 / List of discovered signals
        scan_time: 扫描时间 / Scan timestamp
        interface: 使用的网络接口 / Network interface used
        location: 位置描述（可选）/ Location description (optional)
        platform: 操作系统平台 / Operating system platform
        scan_duration: 扫描耗时（秒）/ Scan duration in seconds
        error: 错误信息（如果有）/ Error message (if any)
    """
    signals: List[WiFiSignal] = field(default_factory=list)
    scan_time: float = field(default_factory=time.time)
    interface: str = ""
    location: str = ""
    platform: str = ""
    scan_duration: float = 0.0
    error: Optional[str] = None

    @property
    def signal_count(self) -> int:
        """信号数量 / Number of signals"""
        return len(self.signals)

    @property
    def strongest_signal(self) -> Optional[WiFiSignal]:
        """最强信号 / Strongest signal"""
        if not self.signals:
            return None
        return max(self.signals, key=lambda s: s.rssi)

    @property
    def weakest_signal(self) -> Optional[WiFiSignal]:
        """最弱信号 / Weakest signal"""
        if not self.signals:
            return None
        return min(self.signals, key=lambda s: s.rssi)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "signal_count": self.signal_count,
            "scan_time": self.scan_time,
            "interface": self.interface,
            "location": self.location,
            "platform": self.platform,
            "scan_duration": self.scan_duration,
            "error": self.error,
            "signals": [s.to_dict() for s in self.signals],
        }

    def to_json(self, indent: int = 2) -> str:
        """转换为JSON字符串 / Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class SignalStatistics:
    """
    信号统计数据模型 / Signal Statistics Data Model
    =================================================
    信号强度的统计摘要信息。
    Statistical summary of signal strength.

    Attributes / 属性:
        mean: 平均值 / Mean value
        median: 中位数 / Median value
        std_dev: 标准差 / Standard deviation
        variance: 方差 / Variance
        min_val: 最小值 / Minimum value
        max_val: 最大值 / Maximum value
        count: 样本数量 / Sample count
    """
    mean: float = 0.0
    median: float = 0.0
    std_dev: float = 0.0
    variance: float = 0.0
    min_val: float = 0.0
    max_val: float = 0.0
    count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return asdict(self)


@dataclass
class Anomaly:
    """
    异常检测结果 / Anomaly Detection Result
    ========================================
    表示一个检测到的信号异常。
    Represents a detected signal anomaly.

    Attributes / 属性:
        ssid: 网络名称 / Network name
        bssid: MAC地址 / MAC address
        rssi: 异常信号值 / Anomalous signal value
        z_score: Z-Score值 / Z-Score value
        timestamp: 检测时间 / Detection timestamp
        description: 异常描述 / Anomaly description
    """
    ssid: str = ""
    bssid: str = ""
    rssi: int = 0
    z_score: float = 0.0
    timestamp: float = field(default_factory=time.time)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return asdict(self)


@dataclass
class TrendResult:
    """
    趋势分析结果 / Trend Analysis Result
    ====================================
    线性回归趋势分析的结果。
    Result of linear regression trend analysis.

    Attributes / 属性:
        slope: 斜率（dBm/次）/ Slope (dBm per sample)
        intercept: 截距 / Intercept
        direction: 趋势方向 / Trend direction
        confidence: 趋势置信度 / Trend confidence (0-1)
    """
    slope: float = 0.0
    intercept: float = 0.0
    direction: str = "stable"   # rising / falling / stable
    confidence: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return asdict(self)


@dataclass
class AnalysisResult:
    """
    分析结果数据模型 / Analysis Result Data Model
    =============================================
    包含统计分析、异常检测和趋势分析的完整结果。
    Complete result containing statistics, anomalies, and trends.

    Attributes / 属性:
        statistics: 信号统计 / Signal statistics
        anomalies: 异常列表 / List of anomalies
        trends: 趋势分析结果（按BSSID索引）/ Trend results indexed by BSSID
        analysis_time: 分析时间 / Analysis timestamp
    """
    statistics: Optional[SignalStatistics] = None
    anomalies: List[Anomaly] = field(default_factory=list)
    trends: Dict[str, TrendResult] = field(default_factory=dict)
    analysis_time: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "statistics": self.statistics.to_dict() if self.statistics else None,
            "anomalies": [a.to_dict() for a in self.anomalies],
            "trends": {k: v.to_dict() for k, v in self.trends.items()},
            "analysis_time": self.analysis_time,
        }


@dataclass
class SignalRecord:
    """
    单条信号历史记录 / Single Signal History Record
    =================================================
    用于构建信号时间序列的记录单元。
    Record unit for building signal time series.

    Attributes / 属性:
        ssid: 网络名称 / Network name
        bssid: MAC地址 / MAC address
        rssi: 信号强度 / Signal strength
        timestamp: 记录时间 / Record timestamp
    """
    ssid: str = ""
    bssid: str = ""
    rssi: int = 0
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return asdict(self)


@dataclass
class SignalHistory:
    """
    信号历史记录数据模型 / Signal History Data Model
    ================================================
    存储多次扫描的信号时间序列数据。
    Stores signal time series data from multiple scans.

    Attributes / 属性:
        records: 历史记录列表 / List of historical records
        metadata: 元数据 / Metadata
        start_time: 起始时间 / Start time
        end_time: 结束时间 / End time
    """
    records: List[SignalRecord] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    start_time: float = 0.0
    end_time: float = 0.0

    def add_record(self, record: SignalRecord) -> None:
        """添加记录 / Add a record"""
        self.records.append(record)
        if not self.start_time or record.timestamp < self.start_time:
            self.start_time = record.timestamp
        if not self.end_time or record.timestamp > self.end_time:
            self.end_time = record.timestamp

    def get_by_bssid(self, bssid: str) -> List[SignalRecord]:
        """按BSSID筛选记录 / Filter records by BSSID"""
        return [r for r in self.records if r.bssid == bssid]

    def get_rssi_series(self, bssid: str) -> List[int]:
        """获取指定BSSID的RSSI时间序列 / Get RSSI time series for a BSSID"""
        return [r.rssi for r in self.get_by_bssid(bssid)]

    @property
    def unique_bssids(self) -> List[str]:
        """获取所有唯一BSSID / Get all unique BSSIDs"""
        seen: set = set()
        result: List[str] = []
        for r in self.records:
            if r.bssid not in seen:
                seen.add(r.bssid)
                result.append(r.bssid)
        return result

    @property
    def record_count(self) -> int:
        """记录总数 / Total record count"""
        return len(self.records)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典 / Convert to dictionary"""
        return {
            "record_count": self.record_count,
            "unique_bssids": self.unique_bssids,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "metadata": self.metadata,
            "records": [r.to_dict() for r in self.records],
        }


def classify_signal(rssi: int) -> SignalLevel:
    """
    根据RSSI值分类信号强度 / Classify signal strength by RSSI value
    =================================================================
    基于常见WiFi信号强度分级标准。
    Based on common WiFi signal strength classification standards.

    Args / 参数:
        rssi: 信号强度值（dBm）/ Signal strength value in dBm

    Returns / 返回:
        SignalLevel: 信号等级枚举 / Signal level enumeration

    分级标准 / Classification Standards:
        - 极强 (Excellent):  -30 ~ -50 dBm  (近距离/Close range)
        - 强 (Strong):       -50 ~ -60 dBm
        - 中 (Good):         -60 ~ -70 dBm
        - 弱 (Weak):         -70 ~ -80 dBm
        - 极弱 (Very Weak):  < -80 dBm      (远距离/Far range)
    """
    if rssi >= -50:
        return SignalLevel.EXCELLENT
    elif rssi >= -60:
        return SignalLevel.STRONG
    elif rssi >= -70:
        return SignalLevel.GOOD
    elif rssi >= -80:
        return SignalLevel.WEAK
    else:
        return SignalLevel.VERY_WEAK
