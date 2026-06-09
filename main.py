#!/usr/bin/env python3
"""
WaveSense-CLI - Main Entry Point
主程序入口

Wi-Fi CSI Motion Detection Engine
Wi-Fi信道状态信息运动检测引擎

Usage:
    python main.py [options]
    python main.py --source simulated --pattern periodic
    python main.py --source pcap --file capture.pcap
    python main.py --source linux --interface wlan0 --channel 36
    python main.py --csv output.csv --mqtt --broker 192.168.1.100
"""

import argparse
import signal
import sys
import time
import math
from typing import Optional

from wavesense.core.csi_reader import (
    CSIReader, SimulatedCSIReader, PcapCSIReader, LinuxCSIReader
)
from wavesense.core.preprocessor import CSIPreprocessor
from wavesense.detection.amplitude_detector import AmplitudeDetector
from wavesense.detection.phase_detector import PhaseDetector
from wavesense.detection.correlation_detector import CorrelationDetector
from wavesense.detection.fusion_engine import FusionEngine
from wavesense.ui.dashboard import Dashboard
from wavesense.output.csv_exporter import CSVExporter
from wavesense.output.mqtt_publisher import MQTTPublisher
from wavesense.utils.config import WaveSenseConfig
from wavesense.utils.logger import Logger


class WaveSenseApp:
    """Main WaveSense application"""

    def __init__(self, config: WaveSenseConfig):
        self.config = config
        self.logger = Logger(level="INFO")
        self.reader: Optional[CSIReader] = None
        self.preprocessor: Optional[CSIPreprocessor] = None
        self.detectors = {}
        self.fusion: Optional[FusionEngine] = None
        self.dashboard: Optional[Dashboard] = None
        self.csv_exporter: Optional[CSVExporter] = None
        self.mqtt: Optional[MQTTPublisher] = None
        self._running = False
        self._frame_count = 0
        self._last_fps_time = 0.0
        self._fps = 0.0

    def setup(self) -> bool:
        """Initialize all components"""
        self.logger.info("🚀 Initializing WaveSense-CLI...")

        # Setup CSI reader
        if self.config.source_type == "simulated":
            self.reader = SimulatedCSIReader(
                num_subcarriers=self.config.num_subcarriers,
                sample_rate=self.config.sample_rate,
                motion_pattern=self.config.motion_pattern,
                noise_level=self.config.noise_level,
                motion_intensity=self.config.motion_intensity
            )
            self.logger.info(f"📡 Using simulated CSI source (pattern: {self.config.motion_pattern})")

        elif self.config.source_type == "pcap":
            if not self.config.pcap_file:
                self.logger.error("❌ pcap file not specified")
                return False
            self.reader = PcapCSIReader(self.config.pcap_file)
            self.logger.info(f"📁 Reading from pcap: {self.config.pcap_file}")

        elif self.config.source_type == "linux":
            self.reader = LinuxCSIReader(
                interface=self.config.interface,
                channel=self.config.channel
            )
            self.logger.info(f"🐧 Using Linux interface: {self.config.interface}")

        else:
            self.logger.error(f"❌ Unknown source type: {self.config.source_type}")
            return False

        # Setup preprocessor
        self.preprocessor = CSIPreprocessor(
            window_size=self.config.window_size,
            filter_type=self.config.filter_type,
            normalize=self.config.normalize
        )

        # Setup detectors
        self.detectors["amplitude"] = AmplitudeDetector(
            threshold=self.config.amplitude_threshold,
            min_duration=self.config.min_duration
        )
        self.detectors["phase"] = PhaseDetector(
            threshold=self.config.phase_threshold,
            min_duration=max(1, self.config.min_duration - 1)
        )
        self.detectors["correlation"] = CorrelationDetector(
            threshold=self.config.correlation_threshold,
            min_duration=max(1, self.config.min_duration - 1)
        )

        # Setup fusion
        self.fusion = FusionEngine(
            method=self.config.fusion_method,
            confirmation_frames=self.config.confirmation_frames
        )

        # Setup dashboard
        if self.config.dashboard_enabled and not self.config.quiet_mode:
            self.dashboard = Dashboard(num_subcarriers=self.config.num_subcarriers)

        # Setup CSV exporter
        if self.config.csv_output:
            self.csv_exporter = CSVExporter(self.config.csv_output)
            self.csv_exporter.open()
            self.csv_exporter.write_header(self.config.num_subcarriers)
            self.logger.info(f"📝 CSV output: {self.config.csv_output}")

        # Setup MQTT
        if self.config.mqtt_enabled:
            self.mqtt = MQTTPublisher(
                broker=self.config.mqtt_broker,
                port=self.config.mqtt_port,
                username=self.config.mqtt_username or None,
                password=self.config.mqtt_password or None,
                topic_prefix=self.config.mqtt_topic_prefix
            )
            if self.mqtt.connect():
                self.mqtt.publish_discovery()
                self.logger.info(f"📤 MQTT connected: {self.config.mqtt_broker}:{self.config.mqtt_port}")
            else:
                self.logger.warning("⚠️ MQTT connection failed")
                self.mqtt = None

        self.logger.info("✅ Initialization complete")
        return True

    def run(self) -> None:
        """Main processing loop"""
        if not self.reader:
            self.logger.error("❌ Reader not initialized")
            return

        self._running = True
        self._last_fps_time = time.time()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info("▶️  Starting detection loop...")

        try:
            with self.reader:
                if self.dashboard:
                    self.dashboard.start()

                for csi in self.reader.read():
                    if not self._running:
                        break

                    self._process_frame(csi)

        except Exception as e:
            self.logger.error(f"❌ Runtime error: {e}")
        finally:
            self._cleanup()

    def _process_frame(self, csi) -> None:
        """Process a single CSI frame"""
        self._frame_count += 1

        # Calculate FPS
        now = time.time()
        elapsed = now - self._last_fps_time
        if elapsed >= 1.0:
            self._fps = self._frame_count / elapsed
            self._frame_count = 0
            self._last_fps_time = now

        # Preprocess
        features = self.preprocessor.process(csi)

        # Run detectors
        results = []
        for name, detector in self.detectors.items():
            result = detector.detect(features)
            results.append(result)

        # Fuse results
        fused = self.fusion.fuse(results)

        # Output
        self._output(features, fused)

    def _output(self, features: dict, fused) -> None:
        """Output results to all enabled sinks"""
        amplitude = features.get("amplitude", [])
        rssi = features.get("rssi", 0.0)
        timestamp = features.get("timestamp", 0.0)

        # Dashboard
        if self.dashboard:
            detector_details = {}
            for name, detector in self.detectors.items():
                if hasattr(detector, '_last_amplitude') and detector._last_amplitude:
                    detector_details[f"{name}_diff"] = getattr(detector, '_history', [0])[-1] if hasattr(detector, '_history') else 0

            self.dashboard.update(
                amplitude=amplitude,
                motion_detected=fused.motion_detected,
                confidence=fused.confidence,
                detector_details=detector_details,
                fps=self._fps
            )

        # CSV
        if self.csv_exporter:
            self.csv_exporter.write_sample(
                timestamp=timestamp,
                rssi=rssi,
                motion_detected=fused.motion_detected,
                confidence=fused.confidence,
                amplitude=amplitude
            )

        # MQTT
        if self.mqtt:
            self.mqtt.publish_motion(
                motion_detected=fused.motion_detected,
                confidence=fused.confidence,
                details={
                    "detector_votes": fused.detector_votes,
                    "fps": round(self._fps, 1)
                }
            )

        # Console log (if no dashboard)
        if not self.dashboard and not self.config.quiet_mode:
            status = "🚨 MOTION" if fused.motion_detected else "  idle   "
            print(f"\r[{status}] conf={fused.confidence:.1%} fps={self._fps:.1f}", end="", flush=True)

    def _signal_handler(self, signum, frame) -> None:
        """Handle shutdown signals"""
        self.logger.info("\n🛑 Shutdown signal received")
        self._running = False

    def _cleanup(self) -> None:
        """Clean up resources"""
        self.logger.info("🧹 Cleaning up...")

        if self.dashboard:
            self.dashboard.stop()

        if self.csv_exporter:
            self.csv_exporter.close()

        if self.mqtt:
            self.mqtt.disconnect()

        self.logger.info("👋 WaveSense stopped")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="WaveSense-CLI - Wi-Fi CSI Motion Detection Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --source simulated --pattern periodic
  %(prog)s --source pcap --file capture.pcap
  %(prog)s --source linux --interface wlan0 --channel 36
  %(prog)s --csv output.csv --mqtt --broker 192.168.1.100
        """
    )

    # Source options
    source_group = parser.add_argument_group("Data Source")
    source_group.add_argument(
        "--source", "-s",
        choices=["simulated", "pcap", "linux"],
        default="simulated",
        help="CSI data source (default: simulated)"
    )
    source_group.add_argument(
        "--file", "-f",
        help="pcap file path"
    )
    source_group.add_argument(
        "--interface", "-i",
        default="wlan0",
        help="Wireless interface (default: wlan0)"
    )
    source_group.add_argument(
        "--channel", "-c",
        type=int,
        default=36,
        help="Wi-Fi channel (default: 36)"
    )
    source_group.add_argument(
        "--pattern", "-p",
        choices=["random", "periodic", "burst"],
        default="random",
        help="Simulated motion pattern (default: random)"
    )
    source_group.add_argument(
        "--subcarriers",
        type=int,
        default=64,
        help="Number of subcarriers (default: 64)"
    )

    # Detection options
    detect_group = parser.add_argument_group("Detection")
    detect_group.add_argument(
        "--threshold",
        type=float,
        default=0.15,
        help="Detection threshold (default: 0.15)"
    )
    detect_group.add_argument(
        "--fusion",
        choices=["majority_vote", "weighted_average", "sequential"],
        default="weighted_average",
        help="Fusion method (default: weighted_average)"
    )

    # Output options
    output_group = parser.add_argument_group("Output")
    output_group.add_argument(
        "--csv",
        help="Export to CSV file"
    )
    output_group.add_argument(
        "--mqtt",
        action="store_true",
        help="Enable MQTT output"
    )
    output_group.add_argument(
        "--broker",
        default="localhost",
        help="MQTT broker address (default: localhost)"
    )
    output_group.add_argument(
        "--port",
        type=int,
        default=1883,
        help="MQTT broker port (default: 1883)"
    )

    # UI options
    ui_group = parser.add_argument_group("UI")
    ui_group.add_argument(
        "--no-dashboard",
        action="store_true",
        help="Disable TUI dashboard"
    )
    ui_group.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode (no console output)"
    )

    # Config
    parser.add_argument(
        "--config",
        help="Load configuration from JSON file"
    )

    args = parser.parse_args()

    # Load or create config
    if args.config:
        config = WaveSenseConfig.from_file(args.config)
    else:
        config = WaveSenseConfig()

    # Override with CLI arguments
    config.source_type = args.source
    config.pcap_file = args.file or config.pcap_file
    config.interface = args.interface
    config.channel = args.channel
    config.motion_pattern = args.pattern
    config.num_subcarriers = args.subcarriers
    config.amplitude_threshold = args.threshold
    config.fusion_method = args.fusion
    config.csv_output = args.csv or config.csv_output
    config.mqtt_enabled = args.mqtt
    config.mqtt_broker = args.broker
    config.mqtt_port = args.port
    config.dashboard_enabled = not args.no_dashboard
    config.quiet_mode = args.quiet

    # Run app
    app = WaveSenseApp(config)
    if app.setup():
        app.run()
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
