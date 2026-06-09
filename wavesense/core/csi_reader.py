"""
CSI Data Reader Module
CSI数据读取模块

Supports multiple CSI data sources:
- Linux nl80211 interface (via iw/iwlist)
- pcap file parsing (offline analysis)
- Simulated data generation (for testing/demo)
"""

import struct
import subprocess
import json
import os
import time
import random
import math
from abc import ABC, abstractmethod
from typing import Iterator, Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class CSIData:
    """CSI data packet structure"""
    timestamp: float
    subcarriers: List[complex]
    rssi: float
    channel: int
    antenna: int
    source: str

    @property
    def amplitude(self) -> List[float]:
        """Extract amplitude from complex subcarriers"""
        return [abs(sc) for sc in self.subcarriers]

    @property
    def phase(self) -> List[float]:
        """Extract phase from complex subcarriers (unwrapped)"""
        raw_phase = [math.atan2(sc.imag, sc.real) for sc in self.subcarriers]
        return self._unwrap_phase(raw_phase)

    def _unwrap_phase(self, phases: List[float]) -> List[float]:
        """Unwrap phase to avoid discontinuities"""
        if not phases:
            return phases
        unwrapped = [phases[0]]
        for i in range(1, len(phases)):
            diff = phases[i] - phases[i - 1]
            while diff > math.pi:
                diff -= 2 * math.pi
            while diff < -math.pi:
                diff += 2 * math.pi
            unwrapped.append(unwrapped[-1] + diff)
        return unwrapped


class CSIReader(ABC):
    """Abstract base class for CSI data readers"""

    @abstractmethod
    def read(self) -> Iterator[CSIData]:
        """Yield CSI data packets"""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the reader and release resources"""
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class SimulatedCSIReader(CSIReader):
    """
    Simulated CSI data generator for testing and demonstration.
    Generates realistic CSI data with configurable motion patterns.
    
    模拟CSI数据生成器，用于测试和演示。
    生成带有可配置运动模式的逼真CSI数据。
    """

    def __init__(
        self,
        num_subcarriers: int = 64,
        sample_rate: float = 100.0,
        motion_pattern: str = "random",
        noise_level: float = 0.1,
        motion_intensity: float = 1.0
    ):
        self.num_subcarriers = num_subcarriers
        self.sample_rate = sample_rate
        self.motion_pattern = motion_pattern
        self.noise_level = noise_level
        self.motion_intensity = motion_intensity
        self._running = False
        self._sample_count = 0

    def _generate_base_signal(self) -> List[complex]:
        """Generate base CSI signal with subcarrier fading pattern"""
        subcarriers = []
        for i in range(self.num_subcarriers):
            # Simulate frequency-selective fading
            freq = (i - self.num_subcarriers / 2) / self.num_subcarriers
            amplitude = 1.0 / (1.0 + 4.0 * freq ** 2)
            phase = 2.0 * math.pi * freq * random.random()
            sc = complex(
                amplitude * math.cos(phase),
                amplitude * math.sin(phase)
            )
            subcarriers.append(sc)
        return subcarriers

    def _apply_motion(self, base: List[complex]) -> List[complex]:
        """Apply motion-induced perturbations to CSI"""
        t = self._sample_count / self.sample_rate
        modified = []

        for i, sc in enumerate(base):
            if self.motion_pattern == "random":
                # Random walk motion
                motion_amp = self.motion_intensity * random.gauss(0, 0.1)
                motion_phase = self.motion_intensity * random.gauss(0, 0.2)
            elif self.motion_pattern == "periodic":
                # Periodic motion (e.g., walking)
                freq = 1.5  # Hz
                motion_amp = self.motion_intensity * 0.3 * math.sin(2 * math.pi * freq * t)
                motion_phase = self.motion_intensity * 0.5 * math.cos(2 * math.pi * freq * t)
            elif self.motion_pattern == "burst":
                # Burst motion (sudden movement)
                burst = 1.0 if (int(t) % 5 < 1) else 0.0
                motion_amp = self.motion_intensity * burst * random.gauss(0, 0.3)
                motion_phase = self.motion_intensity * burst * random.gauss(0, 0.5)
            else:
                motion_amp = 0.0
                motion_phase = 0.0

            # Add noise
            noise_amp = random.gauss(0, self.noise_level)
            noise_phase = random.gauss(0, self.noise_level)

            amp = abs(sc) + motion_amp + noise_amp
            phase = math.atan2(sc.imag, sc.real) + motion_phase + noise_phase

            modified.append(complex(amp * math.cos(phase), amp * math.sin(phase)))

        return modified

    def read(self) -> Iterator[CSIData]:
        """Generate simulated CSI data stream"""
        self._running = True
        base_signal = self._generate_base_signal()

        while self._running:
            start_time = time.time()
            self._sample_count += 1

            modified_signal = self._apply_motion(base_signal.copy())

            csi = CSIData(
                timestamp=time.time(),
                subcarriers=modified_signal,
                rssi=-40.0 + random.gauss(0, 2.0),
                channel=36,
                antenna=0,
                source="simulated"
            )

            yield csi

            # Maintain sample rate
            elapsed = time.time() - start_time
            sleep_time = max(0, 1.0 / self.sample_rate - elapsed)
            time.sleep(sleep_time)

    def close(self) -> None:
        """Stop the simulated reader"""
        self._running = False


class PcapCSIReader(CSIReader):
    """
    Read CSI data from pcap capture files.
    Supports common Wi-Fi CSI capture formats.
    
    从pcap捕获文件中读取CSI数据。
    """

    def __init__(self, filepath: str, chipset: str = "intel"):
        self.filepath = filepath
        self.chipset = chipset
        self._file = None
        self._buffer = b""

    def _parse_pcap_header(self) -> bool:
        """Parse pcap global header"""
        header = self._file.read(24)
        if len(header) < 24:
            return False

        magic = struct.unpack('<I', header[:4])[0]
        if magic == 0xa1b2c3d4:
            self._endian = '<'
        elif magic == 0xd4c3b2a1:
            self._endian = '>'
        else:
            raise ValueError("Invalid pcap file format")

        return True

    def _read_packet(self) -> Optional[bytes]:
        """Read next packet from pcap file"""
        header = self._file.read(16)
        if len(header) < 16:
            return None

        ts_sec, ts_usec, incl_len, orig_len = struct.unpack(
            self._endian + 'IIII', header
        )
        packet_data = self._file.read(incl_len)
        return packet_data

    def _extract_csi_intel(self, packet: bytes) -> Optional[CSIData]:
        """Extract CSI from Intel 5300 format"""
        # Simplified Intel 5300 CSI extraction
        # Real implementation would parse radiotap + CSI header
        if len(packet) < 100:
            return None

        try:
            # Mock extraction for demonstration
            # In real implementation, parse radiotap header + CSI data
            num_sc = 64
            subcarriers = []
            for i in range(num_sc):
                real = struct.unpack('h', packet[50 + i * 4:52 + i * 4])[0] / 1000.0
                imag = struct.unpack('h', packet[52 + i * 4:54 + i * 4])[0] / 1000.0
                subcarriers.append(complex(real, imag))

            return CSIData(
                timestamp=time.time(),
                subcarriers=subcarriers,
                rssi=-45.0,
                channel=36,
                antenna=0,
                source="pcap_intel"
            )
        except Exception:
            return None

    def read(self) -> Iterator[CSIData]:
        """Read CSI data from pcap file"""
        self._file = open(self.filepath, 'rb')

        if not self._parse_pcap_header():
            self._file.close()
            raise ValueError("Failed to parse pcap header")

        while True:
            packet = self._read_packet()
            if packet is None:
                break

            csi = self._extract_csi_intel(packet)
            if csi:
                yield csi

    def close(self) -> None:
        """Close pcap file"""
        if self._file:
            self._file.close()
            self._file = None


class LinuxCSIReader(CSIReader):
    """
    Read CSI data from Linux nl80211 interface.
    Requires compatible wireless card and driver.
    
    从Linux nl80211接口读取CSI数据。
    需要兼容的无线网卡和驱动。
    """

    def __init__(self, interface: str = "wlan0", channel: int = 36):
        self.interface = interface
        self.channel = channel
        self._running = False
        self._process = None

    def _setup_monitor_mode(self) -> bool:
        """Configure interface to monitor mode"""
        try:
            commands = [
                f"ip link set {self.interface} down",
                f"iw dev {self.interface} set type monitor",
                f"ip link set {self.interface} up",
                f"iw dev {self.interface} set channel {self.channel}"
            ]
            for cmd in commands:
                result = subprocess.run(
                    cmd.split(),
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 0:
                    return False
            return True
        except Exception:
            return False

    def read(self) -> Iterator[CSIData]:
        """Read CSI from Linux interface"""
        self._running = True

        if not self._setup_monitor_mode():
            raise RuntimeError(
                f"Failed to setup monitor mode on {self.interface}. "
                "Ensure you have root privileges and compatible hardware."
            )

        # This is a simplified placeholder
        # Real implementation would use raw socket or specific driver interface
        while self._running:
            # Simulate reading from hardware
            time.sleep(0.01)
            yield CSIData(
                timestamp=time.time(),
                subcarriers=[complex(random.gauss(0, 1), random.gauss(0, 1))
                            for _ in range(64)],
                rssi=-50.0,
                channel=self.channel,
                antenna=0,
                source=f"linux_{self.interface}"
            )

    def close(self) -> None:
        """Stop reading and restore interface"""
        self._running = False
        if self._process:
            self._process.terminate()
