"""
MQTT Publisher for Home Assistant Integration
MQTT发布模块（Home Assistant集成）

Publish motion detection results to MQTT broker for Home Assistant integration.
"""

import json
import socket
import struct
import time
from typing import Dict, Optional


class MQTTPublisher:
    """
    Lightweight MQTT client for publishing motion detection results.
    Implements a subset of MQTT 3.1.1 protocol using only standard library.
    """

    def __init__(
        self,
        broker: str = "localhost",
        port: int = 1883,
        client_id: str = "wavesense",
        username: Optional[str] = None,
        password: Optional[str] = None,
        topic_prefix: str = "wavesense"
    ):
        self.broker = broker
        self.port = port
        self.client_id = client_id
        self.username = username
        self.password = password
        self.topic_prefix = topic_prefix
        self._socket: Optional[socket.socket] = None
        self._connected = False

    def connect(self) -> bool:
        """Connect to MQTT broker"""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(5.0)
            self._socket.connect((self.broker, self.port))

            # Send CONNECT packet
            self._send_connect()

            # Receive CONNACK
            response = self._socket.recv(4)
            if len(response) >= 4 and response[3] == 0:
                self._connected = True
                return True
            else:
                self._socket.close()
                self._socket = None
                return False

        except Exception as e:
            print(f"MQTT connection failed: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from MQTT broker"""
        if self._socket:
            try:
                # Send DISCONNECT
                self._socket.send(bytes([0xE0, 0x00]))
                self._socket.close()
            except Exception:
                pass
            finally:
                self._socket = None
                self._connected = False

    def publish_motion(
        self,
        motion_detected: bool,
        confidence: float,
        details: Optional[Dict] = None
    ) -> bool:
        """Publish motion detection result"""
        if not self._connected or not self._socket:
            return False

        payload = {
            "motion_detected": motion_detected,
            "confidence": round(confidence, 4),
            "timestamp": time.time(),
            "details": details or {}
        }

        topic = f"{self.topic_prefix}/motion"
        return self._publish(topic, json.dumps(payload))

    def publish_discovery(self) -> bool:
        """
        Publish Home Assistant MQTT discovery message.
        This creates a binary_sensor entity in Home Assistant.
        """
        if not self._connected:
            return False

        discovery_topic = (
            f"homeassistant/binary_sensor/{self.client_id}/motion/config"
        )

        payload = {
            "name": "WaveSense Motion",
            "state_topic": f"{self.topic_prefix}/motion",
            "value_template": "{{ value_json.motion_detected }}",
            "payload_on": "true",
            "payload_off": "false",
            "device_class": "motion",
            "json_attributes_topic": f"{self.topic_prefix}/motion",
            "unique_id": f"{self.client_id}_motion",
            "device": {
                "identifiers": [self.client_id],
                "name": "WaveSense",
                "model": "CSI Motion Sensor",
                "manufacturer": "WaveSense"
            }
        }

        return self._publish(discovery_topic, json.dumps(payload), retain=True)

    def _send_connect(self) -> None:
        """Build and send MQTT CONNECT packet"""
        # Variable header
        protocol_name = b"\x00\x04MQTT"
        protocol_level = b"\x04"  # MQTT 3.1.1
        connect_flags = 0x02  # Clean session

        if self.username:
            connect_flags |= 0x80
        if self.password:
            connect_flags |= 0x40

        keep_alive = struct.pack(">H", 60)

        # Payload
        client_id_bytes = self.client_id.encode("utf-8")
        client_id_len = struct.pack(">H", len(client_id_bytes))

        payload = client_id_len + client_id_bytes

        if self.username:
            username_bytes = self.username.encode("utf-8")
            payload += struct.pack(">H", len(username_bytes)) + username_bytes

        if self.password:
            password_bytes = self.password.encode("utf-8")
            payload += struct.pack(">H", len(password_bytes)) + password_bytes

        variable_header = protocol_name + protocol_level + bytes([connect_flags]) + keep_alive

        remaining_length = len(variable_header) + len(payload)
        fixed_header = bytes([0x10, remaining_length])

        self._socket.send(fixed_header + variable_header + payload)

    def _publish(self, topic: str, message: str, retain: bool = False) -> bool:
        """Publish message to topic"""
        try:
            topic_bytes = topic.encode("utf-8")
            message_bytes = message.encode("utf-8")

            topic_len = struct.pack(">H", len(topic_bytes))

            fixed_header_byte = 0x30
            if retain:
                fixed_header_byte |= 0x01

            remaining_length = len(topic_len) + len(topic_bytes) + len(message_bytes)
            fixed_header = bytes([fixed_header_byte, remaining_length])

            packet = fixed_header + topic_len + topic_bytes + message_bytes
            self._socket.send(packet)
            return True

        except Exception as e:
            print(f"MQTT publish failed: {e}")
            self._connected = False
            return False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
