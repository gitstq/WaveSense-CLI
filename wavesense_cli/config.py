"""
WaveSense-CLI - 配置管理模块 / Configuration Management Module
=================================================================

管理应用配置，包括默认参数、日志配置、平台检测等。
Manages application configuration, including default parameters,
logging setup, and platform detection.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .models import Platform

# ============================================================
# 版本号 / Version
# ============================================================
__version__ = "1.0.0"
__app_name__ = "WaveSense-CLI"
__description__ = "轻量级终端无线信号智能感知与分析引擎 / Lightweight Terminal Wireless Signal Intelligence & Analysis Engine"

# ============================================================
# 默认配置 / Default Configuration
# ============================================================
DEFAULT_CONFIG: Dict[str, Any] = {
    # 扫描配置 / Scan configuration
    "scan": {
        "interval": 5.0,           # 默认扫描间隔（秒）/ Default scan interval (seconds)
        "timeout": 10.0,           # 扫描超时（秒）/ Scan timeout (seconds)
        "interface": "",           # 默认网络接口 / Default network interface (empty = auto)
        "max_retries": 3,          # 最大重试次数 / Maximum retry attempts
        "cache_ttl": 30.0,         # 缓存有效期（秒）/ Cache TTL (seconds)
    },
    # 分析配置 / Analysis configuration
    "analysis": {
        "z_score_threshold": 2.0,  # 异常检测Z-Score阈值 / Anomaly detection Z-Score threshold
        "min_samples": 5,         # 趋势分析最小样本数 / Minimum samples for trend analysis
        "history_limit": 1000,    # 历史记录上限 / History record limit
    },
    # 可视化配置 / Visualization configuration
    "visualization": {
        "heatmap_width": 60,       # 热力图默认宽度 / Default heatmap width
        "heatmap_height": 20,      # 热力图默认高度 / Default heatmap height
        "chart_height": 15,        # 折线图默认高度 / Default chart height
        "chart_width": 60,        # 折线图默认宽度 / Default chart width
    },
    # 仪表盘配置 / Dashboard configuration
    "dashboard": {
        "refresh_interval": 2.0,  # 仪表盘刷新间隔（秒）/ Dashboard refresh interval (seconds)
        "max_display": 20,        # 最大显示信号数 / Maximum signals to display
    },
    # 导出配置 / Export configuration
    "export": {
        "default_format": "json",  # 默认导出格式 / Default export format
        "output_dir": "./reports", # 默认输出目录 / Default output directory
        "include_timestamp": True, # 文件名包含时间戳 / Include timestamp in filename
    },
    # 日志配置 / Logging configuration
    "logging": {
        "level": "WARNING",        # 默认日志级别 / Default log level
        "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        "date_format": "%Y-%m-%d %H:%M:%S",
    },
}

# ============================================================
# 配置文件路径 / Configuration File Paths
# ============================================================
CONFIG_DIR = Path.home() / ".wavesense"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOG_FILE = CONFIG_DIR / "wavesense.log"
HISTORY_FILE = CONFIG_DIR / "history.json"


class WaveSenseConfig:
    """
    WaveSense配置管理器 / WaveSense Configuration Manager
    ======================================================
    支持从默认值、配置文件和环境变量加载配置。
    Supports loading configuration from defaults, config file, and environment variables.

    优先级（从高到低）/ Priority (high to low):
        1. 环境变量 / Environment variables (WAVESENSE_*)
        2. 配置文件 / Configuration file (~/.wavesense/config.json)
        3. 默认值 / Default values
    """

    def __init__(self) -> None:
        """初始化配置 / Initialize configuration"""
        self._config: Dict[str, Any] = {}
        self._load_defaults()
        self._load_config_file()
        self._load_env_vars()

    def _load_defaults(self) -> None:
        """加载默认配置 / Load default configuration"""
        import copy
        self._config = copy.deepcopy(DEFAULT_CONFIG)

    def _load_config_file(self) -> None:
        """
        从配置文件加载 / Load from configuration file
        如果配置文件不存在则跳过。
        Skip if configuration file does not exist.
        """
        if not CONFIG_FILE.exists():
            return
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                file_config = json.load(f)
            self._deep_merge(self._config, file_config)
        except (json.JSONDecodeError, IOError) as e:
            # 配置文件损坏时使用默认值 / Use defaults when config file is corrupted
            logging.getLogger(__name__).warning(
                "配置文件加载失败，使用默认值: %s / Config file load failed, using defaults: %s", e
            )

    def _load_env_vars(self) -> None:
        """
        从环境变量加载 / Load from environment variables
        环境变量格式: WAVESENSE_SCAN_INTERVAL=5
        Environment variable format: WAVESENSE_SCAN_INTERVAL=5
        """
        env_mapping = {
            "WAVESENSE_SCAN_INTERVAL": ("scan", "interval", float),
            "WAVESENSE_SCAN_TIMEOUT": ("scan", "timeout", float),
            "WAVESENSE_INTERFACE": ("scan", "interface", str),
            "WAVESENSE_Z_SCORE_THRESHOLD": ("analysis", "z_score_threshold", float),
            "WAVESENSE_LOG_LEVEL": ("logging", "level", str),
            "WAVESENSE_EXPORT_FORMAT": ("export", "default_format", str),
            "WAVESENSE_OUTPUT_DIR": ("export", "output_dir", str),
        }
        for env_key, (section, key, type_fn) in env_mapping.items():
            value = os.environ.get(env_key)
            if value is not None:
                try:
                    self._config[section][key] = type_fn(value)
                except (ValueError, TypeError):
                    pass

    @staticmethod
    def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """
        深度合并字典 / Deep merge dictionaries
        将override中的值合并到base中。
        Merge values from override into base.
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                WaveSenseConfig._deep_merge(base[key], value)
            else:
                base[key] = value

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        获取配置值 / Get configuration value

        Args / 参数:
            section: 配置节名 / Configuration section name
            key: 配置键名 / Configuration key name
            default: 默认值 / Default value

        Returns / 返回:
            配置值或默认值 / Configuration value or default
        """
        return self._config.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any) -> None:
        """
        设置配置值 / Set configuration value

        Args / 参数:
            section: 配置节名 / Configuration section name
            key: 配置键名 / Configuration key name
            value: 配置值 / Configuration value
        """
        if section not in self._config:
            self._config[section] = {}
        self._config[section][key] = value

    def save(self) -> None:
        """
        保存配置到文件 / Save configuration to file
        自动创建配置目录。
        Automatically create configuration directory.
        """
        try:
            CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logging.getLogger(__name__).error("配置文件保存失败: %s / Config file save failed: %s", e)

    def to_dict(self) -> Dict[str, Any]:
        """返回配置字典 / Return configuration dictionary"""
        import copy
        return copy.deepcopy(self._config)


# ============================================================
# 平台检测 / Platform Detection
# ============================================================
def detect_platform() -> Platform:
    """
    检测当前操作系统平台 / Detect current operating system platform

    Returns / 返回:
        Platform: 平台枚举 / Platform enumeration
    """
    system = platform.system().lower()
    if system == "linux":
        return Platform.LINUX
    elif system == "darwin":
        return Platform.MACOS
    elif system == "windows":
        return Platform.WINDOWS
    else:
        return Platform.UNKNOWN


def get_platform_info() -> Dict[str, str]:
    """
    获取详细平台信息 / Get detailed platform information

    Returns / 返回:
        包含平台详细信息的字典 / Dictionary with detailed platform info
    """
    return {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python_version": platform.python_version(),
    }


# ============================================================
# 日志配置 / Logging Configuration
# ============================================================
def setup_logging(level: Optional[str] = None) -> logging.Logger:
    """
    配置日志系统 / Configure logging system

    Args / 参数:
        level: 日志级别字符串 / Log level string (DEBUG/INFO/WARNING/ERROR)

    Returns / 返回:
        logging.Logger: 根日志记录器 / Root logger
    """
    config = WaveSenseConfig()
    log_level = level or config.get("logging", "level", "WARNING")
    log_format = config.get("logging", "format")
    date_format = config.get("logging", "date_format")

    # 确保配置目录存在 / Ensure config directory exists
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    except IOError:
        pass

    # 配置根日志记录器 / Configure root logger
    logger = logging.getLogger("wavesense")
    logger.setLevel(getattr(logging, log_level.upper(), logging.WARNING))

    # 避免重复添加处理器 / Avoid duplicate handlers
    if not logger.handlers:
        # 控制台处理器 / Console handler
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(getattr(logging, log_level.upper(), logging.WARNING))
        console_handler.setFormatter(logging.Formatter(log_format, date_format))
        logger.addHandler(console_handler)

        # 文件处理器（可选）/ File handler (optional)
        try:
            file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(logging.Formatter(log_format, date_format))
            logger.addHandler(file_handler)
        except IOError:
            pass

    return logger


# ============================================================
# 全局配置实例 / Global Configuration Instance
# ============================================================
_config_instance: Optional[WaveSenseConfig] = None


def get_config() -> WaveSenseConfig:
    """
    获取全局配置单例 / Get global configuration singleton

    Returns / 返回:
        WaveSenseConfig: 配置实例 / Configuration instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = WaveSenseConfig()
    return _config_instance
