"""
Configuration Manager
配置管理模块

Manage WaveSense configuration from files and command-line arguments.
"""

import json
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class WaveSenseConfig:
    """WaveSense configuration"""
    # Data source
    source_type: str = "simulated"  # simulated, pcap, linux
    pcap_file: str = ""
    interface: str = "wlan0"
    channel: int = 36
    num_subcarriers: int = 64
    sample_rate: float = 100.0

    # Simulator settings
    motion_pattern: str = "random"  # random, periodic, burst
    noise_level: float = 0.1
    motion_intensity: float = 1.0

    # Preprocessor
    window_size: int = 10
    filter_type: str = "median"  # median, mean, ewma
    normalize: bool = True

    # Detectors
    amplitude_threshold: float = 0.15
    phase_threshold: float = 0.3
    correlation_threshold: float = 0.85
    min_duration: int = 3

    # Fusion
    fusion_method: str = "weighted_average"  # majority_vote, weighted_average, sequential
    confirmation_frames: int = 2

    # Output
    csv_output: str = ""
    mqtt_enabled: bool = False
    mqtt_broker: str = "localhost"
    mqtt_port: int = 1883
    mqtt_username: str = ""
    mqtt_password: str = ""
    mqtt_topic_prefix: str = "wavesense"

    # UI
    dashboard_enabled: bool = True
    quiet_mode: bool = False

    @classmethod
    def from_file(cls, filepath: str) -> "WaveSenseConfig":
        """Load configuration from JSON file"""
        config = cls()
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                data = json.load(f)
            for key, value in data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        return config

    def to_file(self, filepath: str) -> None:
        """Save configuration to JSON file"""
        with open(filepath, "w") as f:
            json.dump(asdict(self), f, indent=2)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)
