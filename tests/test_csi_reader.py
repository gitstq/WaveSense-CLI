"""
Unit tests for CSI Reader module
CSI读取模块单元测试
"""

import unittest
import time
from wavesense.core.csi_reader import SimulatedCSIReader, CSIData


class TestSimulatedCSIReader(unittest.TestCase):
    """Test simulated CSI reader"""

    def test_initialization(self):
        """Test reader initialization"""
        reader = SimulatedCSIReader(
            num_subcarriers=64,
            motion_pattern="periodic"
        )
        self.assertEqual(reader.num_subcarriers, 64)
        self.assertEqual(reader.motion_pattern, "periodic")

    def test_data_generation(self):
        """Test CSI data generation"""
        reader = SimulatedCSIReader(num_subcarriers=32)
        
        with reader:
            data = next(reader.read())
            self.assertIsInstance(data, CSIData)
            self.assertEqual(len(data.subcarriers), 32)
            self.assertIsInstance(data.subcarriers[0], complex)
            self.assertTrue(-100 < data.rssi < 0)

    def test_amplitude_extraction(self):
        """Test amplitude extraction"""
        reader = SimulatedCSIReader(num_subcarriers=16)
        
        with reader:
            data = next(reader.read())
            amp = data.amplitude
            self.assertEqual(len(amp), 16)
            self.assertTrue(all(a >= 0 for a in amp))

    def test_phase_extraction(self):
        """Test phase extraction"""
        reader = SimulatedCSIReader(num_subcarriers=16)
        
        with reader:
            data = next(reader.read())
            phase = data.phase
            self.assertEqual(len(phase), 16)

    def test_different_patterns(self):
        """Test different motion patterns"""
        patterns = ["random", "periodic", "burst"]
        
        for pattern in patterns:
            reader = SimulatedCSIReader(motion_pattern=pattern)
            with reader:
                data = next(reader.read())
                self.assertIsInstance(data, CSIData)


class TestCSIData(unittest.TestCase):
    """Test CSIData dataclass"""

    def test_properties(self):
        """Test amplitude and phase properties"""
        subcarriers = [complex(1, 0), complex(0, 1), complex(-1, 0)]
        data = CSIData(
            timestamp=time.time(),
            subcarriers=subcarriers,
            rssi=-50.0,
            channel=36,
            antenna=0,
            source="test"
        )
        
        self.assertEqual(len(data.amplitude), 3)
        self.assertEqual(len(data.phase), 3)
        self.assertAlmostEqual(data.amplitude[0], 1.0)
        self.assertAlmostEqual(data.amplitude[1], 1.0)


if __name__ == "__main__":
    unittest.main()
