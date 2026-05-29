"""
WaveSense-CLI - WiFi信号扫描引擎 / WiFi Signal Scanning Engine
================================================================

跨平台WiFi信号扫描，支持Linux/macOS/Windows。
Cross-platform WiFi signal scanning, supporting Linux/macOS/Windows.

使用系统命令获取WiFi信号数据并标准化输出。
Uses system commands to obtain WiFi signal data and standardizes output.

支持命令 / Supported commands:
    - Linux:   nmcli device wifi list / iwlist scan
    - macOS:   airport -s
    - Windows: netsh wlan show networks mode=bssid
"""

from __future__ import annotations

import logging
import re
import time
from typing import Callable, Dict, List, Optional, Tuple

from .config import detect_platform, get_config
from .models import Platform, ScanResult, WiFiSignal
from .utils import run_command

logger = logging.getLogger("wavesense.scanner")


# ============================================================
# 自定义异常 / Custom Exceptions
# ============================================================
class ScanError(Exception):
    """扫描错误基类 / Base scan error"""
    pass


class PlatformNotSupportedError(ScanError):
    """平台不支持错误 / Platform not supported error"""
    pass


class ScanCommandNotFoundError(ScanError):
    """扫描命令未找到错误 / Scan command not found error"""
    pass


class ScanTimeoutError(ScanError):
    """扫描超时错误 / Scan timeout error"""
    pass


class ScanPermissionError(ScanError):
    """扫描权限错误 / Scan permission error"""
    pass


# ============================================================
# 解析器注册 / Parser Registration
# ============================================================
# 各平台的扫描命令和解析函数 / Scan commands and parser functions for each platform
PLATFORM_SCANNERS: Dict[Platform, List[Dict[str, any]]] = {
    Platform.LINUX: [
        {
            "name": "nmcli",
            "command": ["nmcli", "-t", "-f", "SSID,BSSID,CHAN,FREQ,SIGNAL,SECURITY,DEVICE", "device", "wifi", "list", "--rescan", "yes"],
            "parser": "_parse_nmcli_output",
        },
        {
            "name": "iwlist",
            "command": ["iwlist", "scan"],
            "parser": "_parse_iwlist_output",
        },
    ],
    Platform.MACOS: [
        {
            "name": "airport",
            "command": ["/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport", "-s"],
            "parser": "_parse_airport_output",
        },
    ],
    Platform.WINDOWS: [
        {
            "name": "netsh",
            "command": ["netsh", "wlan", "show", "networks", "mode=bssid"],
            "parser": "_parse_netsh_output",
        },
    ],
}


class WiFiScanner:
    """
    WiFi信号扫描器 / WiFi Signal Scanner
    ======================================
    跨平台WiFi信号扫描引擎，支持持续监控模式。
    Cross-platform WiFi signal scanning engine with continuous monitoring support.

    Usage / 用法:
        scanner = WiFiScanner()
        result = scanner.scan()
        for signal in result.signals:
            print(signal)
    """

    def __init__(
        self,
        interface: str = "",
        timeout: Optional[float] = None,
        cache_ttl: Optional[float] = None,
    ) -> None:
        """
        初始化扫描器 / Initialize scanner

        Args / 参数:
            interface: 指定网络接口 / Specify network interface
            timeout: 扫描超时时间 / Scan timeout
            cache_ttl: 缓存有效期 / Cache TTL
        """
        self._interface = interface
        config = get_config()
        self._timeout = timeout or config.get("scan", "timeout", 10.0)
        self._cache_ttl = cache_ttl or config.get("scan", "cache_ttl", 30.0)
        self._max_retries = config.get("scan", "max_retries", 3)
        self._cache: Optional[ScanResult] = None
        self._cache_time: float = 0.0
        self._platform = detect_platform()
        self._history: List[ScanResult] = []

        logger.debug("扫描器初始化 / Scanner initialized: platform=%s, interface=%s",
                      self._platform.value, self._interface)

    @property
    def platform(self) -> Platform:
        """当前平台 / Current platform"""
        return self._platform

    @property
    def interface(self) -> str:
        """当前网络接口 / Current network interface"""
        return self._interface

    @interface.setter
    def interface(self, value: str) -> None:
        """设置网络接口 / Set network interface"""
        self._interface = value

    @property
    def cache(self) -> Optional[ScanResult]:
        """获取缓存结果 / Get cached result"""
        if self._cache and (time.time() - self._cache_time) < self._cache_ttl:
            return self._cache
        return None

    def clear_cache(self) -> None:
        """清除缓存 / Clear cache"""
        self._cache = None
        self._cache_time = 0.0

    def scan(self, use_cache: bool = False) -> ScanResult:
        """
        执行一次WiFi信号扫描 / Perform a single WiFi signal scan

        Args / 参数:
            use_cache: 是否使用缓存 / Whether to use cache

        Returns / 返回:
            ScanResult: 扫描结果 / Scan result

        Raises / 异常:
            PlatformNotSupportedError: 平台不支持 / Platform not supported
            ScanCommandNotFoundError: 扫描命令未找到 / Scan command not found
        """
        # 检查缓存 / Check cache
        if use_cache:
            cached = self.cache
            if cached:
                logger.debug("使用缓存结果 / Using cached result")
                return cached

        # 检查平台支持 / Check platform support
        if self._platform == Platform.UNKNOWN:
            raise PlatformNotSupportedError(
                f"不支持的平台 / Unsupported platform: {self._platform}"
            )

        scanners = PLATFORM_SCANNERS.get(self._platform, [])
        if not scanners:
            raise PlatformNotSupportedError(
                f"没有可用的扫描器 / No available scanners for platform: {self._platform.value}"
            )

        # 尝试每个扫描命令 / Try each scan command
        last_error: Optional[Exception] = None
        for scanner_info in scanners:
            for attempt in range(self._max_retries):
                try:
                    result = self._execute_scan(scanner_info)
                    # 更新缓存 / Update cache
                    self._cache = result
                    self._cache_time = time.time()
                    self._history.append(result)
                    return result
                except ScanError as e:
                    last_error = e
                    logger.debug("扫描尝试 %d/%d 失败: %s / Scan attempt %d/%d failed: %s",
                                 attempt + 1, self._max_retries, e, attempt + 1, self._max_retries, e)
                    if attempt < self._max_retries - 1:
                        time.sleep(1.0)

        # 所有扫描器都失败 / All scanners failed
        error_msg = f"所有扫描命令均失败 / All scan commands failed"
        if last_error:
            error_msg += f": {last_error}"
        logger.error(error_msg)

        return ScanResult(
            signals=[],
            interface=self._interface,
            platform=self._platform.value,
            error=error_msg,
        )

    def _execute_scan(self, scanner_info: Dict[str, any]) -> ScanResult:
        """
        执行单个扫描命令 / Execute a single scan command

        Args / 参数:
            scanner_info: 扫描器信息 / Scanner info dictionary

        Returns / 返回:
            ScanResult: 扫描结果 / Scan result
        """
        cmd = scanner_info["command"]
        parser_name = scanner_info["parser"]

        # 如果指定了接口，添加到命令中 / Add interface to command if specified
        if self._interface:
            if self._platform == Platform.LINUX and scanner_info["name"] == "nmcli":
                cmd = cmd + ["ifname", self._interface]
            elif self._platform == Platform.LINUX and scanner_info["name"] == "iwlist":
                cmd = [cmd[0], self._interface, "scan"]

        logger.debug("执行扫描命令 / Executing scan command: %s", " ".join(cmd))

        start_time = time.time()
        returncode, stdout, stderr = run_command(cmd, timeout=self._timeout)
        duration = time.time() - start_time

        if returncode != 0:
            # 检查特定错误类型 / Check specific error types
            if "Permission denied" in stderr or "not allowed" in stderr.lower():
                raise ScanPermissionError(f"权限不足: {stderr.strip()} / Permission denied: {stderr.strip()}")
            if "not found" in stderr.lower() or returncode == 127:
                raise ScanCommandNotFoundError(f"命令未找到: {cmd[0]} / Command not found: {cmd[0]}")
            raise ScanError(f"扫描命令返回错误码 {returncode}: {stderr.strip()} / "
                           f"Scan command returned error code {returncode}: {stderr.strip()}")

        if not stdout.strip():
            raise ScanError("扫描命令无输出 / Scan command produced no output")

        # 解析输出 / Parse output
        parser_func = getattr(self, parser_name)
        signals = parser_func(stdout)

        logger.debug("扫描完成 / Scan completed: %d signals found in %ss",
                      len(signals), f"{duration:.2f}")

        return ScanResult(
            signals=signals,
            scan_time=start_time,
            interface=self._interface,
            platform=self._platform.value,
            scan_duration=duration,
        )

    # ============================================================
    # Linux解析器 / Linux Parsers
    # ============================================================
    def _parse_nmcli_output(self, output: str) -> List[WiFiSignal]:
        """
        解析nmcli命令输出 / Parse nmcli command output
        ==================================================
        nmcli -t -f SSID,BSSID,CHAN,FREQ,SIGNAL,SECURITY,DEVICE device wifi list

        输出格式 / Output format (colon-separated):
            SSID:BSSID:CHAN:FREQ:SIGNAL:SECURITY:DEVICE

        注意：SSID和BSSID都可能包含冒号，需通过BSSID的MAC格式定位。
        Note: Both SSID and BSSID may contain colons, locate by BSSID MAC format.

        Args / 参数:
            output: nmcli原始输出 / Raw nmcli output

        Returns / 返回:
            WiFi信号列表 / List of WiFi signals
        """
        signals: List[WiFiSignal] = []
        now = time.time()

        for line in output.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("SSID"):
                continue

            try:
                # 通过BSSID的MAC地址格式定位字段位置
                # Locate field positions by BSSID MAC address format
                # BSSID格式: XX:XX:XX:XX:XX:XX (5个冒号)
                # 在行中查找BSSID位置
                bssid_match = re.search(
                    r"(?:^|:)([0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2})(?=:)",
                    line
                )
                if not bssid_match:
                    continue

                bssid = bssid_match.group(1).upper()
                bssid_end = bssid_match.end()

                # BSSID后面的字段: CHAN:FREQ:SIGNAL:SECURITY:DEVICE
                after_bssid = line[bssid_end + 1:]  # 跳过BSSID后面的冒号
                after_parts = after_bssid.split(":")

                if len(after_parts) < 5:
                    continue

                channel = int(after_parts[0]) if after_parts[0].strip().isdigit() else 0
                frequency = int(after_parts[1]) if after_parts[1].strip().isdigit() else 0
                signal_pct = int(after_parts[2]) if after_parts[2].strip().isdigit() else 0
                security = after_parts[3].strip()
                interface = after_parts[4].strip()

                # nmcli信号强度是0-100的百分比，转换为dBm
                # nmcli signal is 0-100 percentage, convert to dBm
                # nmcli uses 0-100 where 100 = -30 dBm, 0 = -100 dBm
                rssi = int(-100 + (signal_pct * 70 / 100)) if signal_pct > 0 else -100

                # SSID是BSSID之前的部分
                # SSID is the part before BSSID
                bssid_start = bssid_match.start(1)
                ssid_prefix = line[:bssid_start]
                # 去掉末尾的冒号（如果有）/ Remove trailing colon if present
                if ssid_prefix.endswith(":"):
                    ssid_prefix = ssid_prefix[:-1]
                ssid = ssid_prefix.strip()

                signals.append(WiFiSignal(
                    ssid=ssid,
                    bssid=bssid,
                    rssi=rssi,
                    channel=channel,
                    frequency=frequency,
                    security=security,
                    timestamp=now,
                    interface=interface or self._interface,
                ))
            except (ValueError, IndexError) as e:
                logger.debug("解析nmcli行失败 / Failed to parse nmcli line: %s, error: %s", line, e)
                continue

        return signals

    def _parse_iwlist_output(self, output: str) -> List[WiFiSignal]:
        """
        解析iwlist命令输出 / Parse iwlist command output
        ===================================================
        iwlist <interface> scan

        输出格式示例 / Output format example:
            Cell 01 - Address: AA:BB:CC:DD:EE:FF
                ESSID:"NetworkName"
                Protocol:IEEE 802.11bg
                Mode:Managed
                Frequency:2.412 GHz (Channel 1)
                Quality:70/100  Signal level:-60 dBm
                Encryption key:on
                IE: WPA Version 1

        Args / 参数:
            output: iwlist原始输出 / Raw iwlist output

        Returns / 返回:
            WiFi信号列表 / List of WiFi signals
        """
        signals: List[WiFiSignal] = []
        now = time.time()

        # 按Cell分割 / Split by Cell
        cell_blocks = re.split(r"Cell \d+ -", output)

        for block in cell_blocks[1:]:  # 跳过第一个空块 / Skip first empty block
            try:
                # 提取BSSID / Extract BSSID
                bssid_match = re.search(r"Address:\s*([0-9A-Fa-f:]{17})", block)
                bssid = bssid_match.group(1).upper() if bssid_match else ""

                # 提取SSID / Extract SSID
                ssid_match = re.search(r'ESSID:"([^"]*)"', block)
                ssid = ssid_match.group(1) if ssid_match else ""

                # 提取信道 / Extract channel
                channel_match = re.search(r"[Cc]hannel[:\s]*(\d+)", block)
                channel = int(channel_match.group(1)) if channel_match else 0

                # 提取频率 / Extract frequency
                freq_match = re.search(r"Frequency:(\d+(?:\.\d+)?)\s*GHz", block)
                frequency = int(float(freq_match.group(1)) * 1000) if freq_match else 0

                # 提取信号强度 / Extract signal level
                rssi_match = re.search(r"Signal level[=:]\s*(-?\d+)\s*dBm", block)
                if not rssi_match:
                    # 尝试Quality格式 / Try Quality format
                    quality_match = re.search(r"Quality[=:]\s*(\d+)/(\d+)", block)
                    if quality_match:
                        q = int(quality_match.group(1))
                        q_max = int(quality_match.group(2))
                        rssi = int(-100 + (q / q_max) * 70) if q_max > 0 else -100
                    else:
                        rssi = -100
                else:
                    rssi = int(rssi_match.group(1))

                # 提取加密信息 / Extract encryption info
                security = ""
                enc_match = re.search(r"Encryption key:(on|off)", block)
                if enc_match and enc_match.group(1) == "on":
                    if "WPA2" in block:
                        security = "WPA2"
                    elif "WPA" in block:
                        security = "WPA"
                    elif "WEP" in block:
                        security = "WEP"
                    else:
                        security = "WPA/WPA2"

                signals.append(WiFiSignal(
                    ssid=ssid,
                    bssid=bssid,
                    rssi=rssi,
                    channel=channel,
                    frequency=frequency,
                    security=security,
                    timestamp=now,
                    interface=self._interface,
                ))
            except (ValueError, AttributeError) as e:
                logger.debug("解析iwlist块失败 / Failed to parse iwlist block: %s", e)
                continue

        return signals

    # ============================================================
    # macOS解析器 / macOS Parsers
    # ============================================================
    def _parse_airport_output(self, output: str) -> List[WiFiSignal]:
        """
        解析airport命令输出 / Parse airport command output
        =====================================================
        airport -s

        输出格式 / Output format (space-separated):
            SSID                             BSSID             RSSI  CHANNEL  HT
            MyNetwork                        AA:BB:CC:DD:EE:FF -65   6       Y

        Args / 参数:
            output: airport原始输出 / Raw airport output

        Returns / 返回:
            WiFi信号列表 / List of WiFi signals
        """
        signals: List[WiFiSignal] = []
        now = time.time()

        lines = output.strip().split("\n")
        for line in lines[1:]:  # 跳过标题行 / Skip header line
            parts = line.split()
            if len(parts) < 4:
                continue

            try:
                # airport输出SSID可能包含空格，需要特殊处理
                # airport output SSID may contain spaces, needs special handling
                # 格式: SSID(可含空格) BSSID RSSI CHANNEL [其他字段]
                # BSSID总是MAC地址格式
                bssid_idx = None
                for i, part in enumerate(parts):
                    if re.match(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$", part):
                        bssid_idx = i
                        break

                if bssid_idx is None:
                    continue

                ssid = " ".join(parts[:bssid_idx])
                bssid = parts[bssid_idx].upper()
                rssi = int(parts[bssid_idx + 1])
                channel = int(parts[bssid_idx + 2]) if bssid_idx + 2 < len(parts) else 0

                # 推断频率 / Infer frequency
                frequency = 0
                if channel > 0:
                    if 1 <= channel <= 14:
                        frequency = 2412 + (channel - 1) * 5
                    elif 36 <= channel <= 165:
                        frequency = 5000 + channel * 5

                signals.append(WiFiSignal(
                    ssid=ssid,
                    bssid=bssid,
                    rssi=rssi,
                    channel=channel,
                    frequency=frequency,
                    security="",
                    timestamp=now,
                    interface=self._interface,
                ))
            except (ValueError, IndexError) as e:
                logger.debug("解析airport行失败 / Failed to parse airport line: %s, error: %s", line, e)
                continue

        return signals

    # ============================================================
    # Windows解析器 / Windows Parsers
    # ============================================================
    def _parse_netsh_output(self, output: str) -> List[WiFiSignal]:
        """
        解析netsh命令输出 / Parse netsh command output
        ==================================================
        netsh wlan show networks mode=bssid

        输出格式示例 / Output format example:
            SSID 1 : MyNetwork
                Network type             : Infrastructure
                Authentication           : WPA2-Personal
                BSSID 1                  : AA:BB:CC:DD:EE:FF
                     Signal             : 75%
                     Channel            : 6

        Args / 参数:
            output: netsh原始输出 / Raw netsh output

        Returns / 返回:
            WiFi信号列表 / List of WiFi signals
        """
        signals: List[WiFiSignal] = []
        now = time.time()

        # 按SSID块分割 / Split by SSID blocks
        # 使用负向前瞻避免匹配BSSID中的SSID / Use negative lookahead to avoid matching SSID in BSSID
        ssid_blocks = re.split(r"(?<!B)SSID \d+\s*:", output)

        for block in ssid_blocks[1:]:
            try:
                lines = block.strip().split("\n")
                if not lines:
                    continue

                # 第一行是SSID名称 / First line is SSID name
                ssid = lines[0].strip()

                # 查找认证方式 / Find authentication
                security = ""
                for line in lines:
                    if "Authentication" in line:
                        security = line.split(":", 1)[1].strip()
                        break

                # 查找所有BSSID / Find all BSSIDs
                bssid_sections = re.split(r"BSSID \d+\s*:", block)
                for bssid_block in bssid_sections[1:]:
                    bssid_lines = bssid_block.strip().split("\n")
                    bssid = ""
                    signal_pct = 0
                    channel = 0

                    for idx, bl in enumerate(bssid_lines):
                        bl_stripped = bl.strip()
                        if not bl_stripped:
                            continue

                        # 第一行可能是BSSID值（MAC地址格式）
                        # First line may be BSSID value (MAC address format)
                        if idx == 0 and re.match(
                            r"^([0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}$", bl_stripped
                        ):
                            bssid = bl_stripped.upper().replace("-", ":")
                            continue

                        # netsh使用 ' : ' (空格-冒号-空格) 作为字段分隔符
                        # netsh uses ' : ' (space-colon-space) as field separator
                        if " : " in bl_stripped:
                            key, _, value = bl_stripped.partition(" : ")
                            key = key.strip()
                            value = value.strip()
                            if "Signal" in key:
                                pct_match = re.search(r"(\d+)%", value)
                                signal_pct = int(pct_match.group(1)) if pct_match else 0
                            elif "Channel" in key:
                                ch_match = re.search(r"(\d+)", value)
                                channel = int(ch_match.group(1)) if ch_match else 0

                    if bssid:
                        # 将百分比转换为dBm / Convert percentage to dBm
                        rssi = int(-100 + (signal_pct * 70 / 100)) if signal_pct > 0 else -100

                        signals.append(WiFiSignal(
                            ssid=ssid,
                            bssid=bssid,
                            rssi=rssi,
                            channel=channel,
                            frequency=0,
                            security=security,
                            timestamp=now,
                            interface=self._interface,
                        ))
            except (ValueError, AttributeError) as e:
                logger.debug("解析netsh块失败 / Failed to parse netsh block: %s", e)
                continue

        return signals

    # ============================================================
    # 持续监控 / Continuous Monitoring
    # ============================================================
    def monitor(
        self,
        callback: Optional[Callable[[ScanResult], None]] = None,
        interval: Optional[float] = None,
        max_scans: Optional[int] = None,
    ) -> List[ScanResult]:
        """
        持续监控WiFi信号 / Continuously monitor WiFi signals
        ======================================================

        Args / 参数:
            callback: 每次扫描后的回调函数 / Callback after each scan
            interval: 扫描间隔（秒）/ Scan interval in seconds
            max_scans: 最大扫描次数 / Maximum number of scans

        Returns / 返回:
            所有扫描结果的列表 / List of all scan results
        """
        config = get_config()
        scan_interval = interval or config.get("scan", "interval", 5.0)
        results: List[ScanResult] = []
        scan_count = 0

        logger.info("开始持续监控 / Starting continuous monitoring: interval=%.1fs", scan_interval)

        try:
            while max_scans is None or scan_count < max_scans:
                result = self.scan(use_cache=False)
                results.append(result)
                scan_count += 1

                if callback:
                    callback(result)

                if max_scans is not None and scan_count >= max_scans:
                    break

                time.sleep(scan_interval)
        except KeyboardInterrupt:
            logger.info("监控已停止（用户中断）/ Monitoring stopped (user interrupt)")

        return results

    def get_history(self) -> List[ScanResult]:
        """获取扫描历史 / Get scan history"""
        return self._history

    def clear_history(self) -> None:
        """清除扫描历史 / Clear scan history"""
        self._history.clear()
