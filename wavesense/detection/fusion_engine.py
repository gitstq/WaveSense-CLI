"""
Multi-Algorithm Fusion Engine
多算法融合决策引擎

Combines outputs from multiple detectors using weighted voting
and temporal consistency to improve detection accuracy.
"""

import statistics
from typing import Dict, List, Optional, Deque
from collections import deque
from dataclasses import dataclass
from .amplitude_detector import DetectionResult


@dataclass
class FusionResult:
    """Fused detection result"""
    timestamp: float
    motion_detected: bool
    confidence: float
    detector_votes: Dict[str, bool]
    detector_confidences: Dict[str, float]
    fusion_method: str


class FusionEngine:
    """
    Fusion engine that combines multiple detector outputs.
    
    Supports multiple fusion strategies:
    - majority_vote: Simple majority voting
    - weighted_average: Weighted by detector confidence
    - sequential: Require sequential confirmation
    """

    def __init__(
        self,
        method: str = "weighted_average",
        weights: Optional[Dict[str, float]] = None,
        confirmation_frames: int = 2,
        history_size: int = 20
    ):
        self.method = method
        self.confirmation_frames = confirmation_frames
        self.history_size = history_size

        # Default weights
        self.weights = weights or {
            "amplitude": 0.35,
            "phase": 0.35,
            "correlation": 0.30
        }

        self._history: Deque[FusionResult] = deque(maxlen=history_size)
        self._confirmation_count = 0

    def fuse(self, results: List[DetectionResult]) -> FusionResult:
        """
        Fuse multiple detector results into single decision.
        
        Args:
            results: List of DetectionResult from individual detectors
        
        Returns:
            FusionResult with combined decision
        """
        if not results:
            return FusionResult(
                timestamp=0.0,
                motion_detected=False,
                confidence=0.0,
                detector_votes={},
                detector_confidences={},
                fusion_method=self.method
            )

        timestamp = results[0].timestamp
        votes = {}
        confidences = {}

        for r in results:
            votes[r.detector_type] = r.motion_detected
            confidences[r.detector_type] = r.confidence

        # Apply fusion method
        if self.method == "majority_vote":
            motion_detected, confidence = self._majority_vote(votes, confidences)
        elif self.method == "weighted_average":
            motion_detected, confidence = self._weighted_average(votes, confidences)
        elif self.method == "sequential":
            motion_detected, confidence = self._sequential(votes, confidences)
        else:
            motion_detected, confidence = self._weighted_average(votes, confidences)

        # Apply temporal confirmation
        if motion_detected:
            self._confirmation_count += 1
        else:
            self._confirmation_count = 0

        final_detection = self._confirmation_count >= self.confirmation_frames

        # Adjust confidence based on confirmation
        if final_detection:
            confidence = min(1.0, confidence * (1.0 + 0.1 * self._confirmation_count))

        result = FusionResult(
            timestamp=timestamp,
            motion_detected=final_detection,
            confidence=confidence,
            detector_votes=votes,
            detector_confidences=confidences,
            fusion_method=self.method
        )

        self._history.append(result)
        return result

    def _majority_vote(
        self,
        votes: Dict[str, bool],
        confidences: Dict[str, float]
    ) -> tuple:
        """Simple majority voting"""
        true_count = sum(1 for v in votes.values() if v)
        total = len(votes)
        motion_detected = true_count > total / 2
        confidence = statistics.mean(confidences.values()) if confidences else 0.0
        return motion_detected, confidence

    def _weighted_average(
        self,
        votes: Dict[str, bool],
        confidences: Dict[str, float]
    ) -> tuple:
        """Weighted average of detector confidences"""
        total_weight = 0.0
        weighted_sum = 0.0

        for detector, vote in votes.items():
            weight = self.weights.get(detector, 1.0)
            conf = confidences.get(detector, 0.0)
            weighted_sum += weight * conf
            total_weight += weight

        avg_confidence = weighted_sum / total_weight if total_weight > 0 else 0.0
        motion_detected = avg_confidence > 0.5

        return motion_detected, avg_confidence

    def _sequential(
        self,
        votes: Dict[str, bool],
        confidences: Dict[str, float]
    ) -> tuple:
        """Require all detectors to agree"""
        motion_detected = all(votes.values())
        confidence = min(confidences.values()) if confidences else 0.0
        return motion_detected, confidence

    def get_statistics(self) -> Dict:
        """Get fusion statistics over history"""
        if not self._history:
            return {}

        detections = [r.motion_detected for r in self._history]
        confidences = [r.confidence for r in self._history]

        return {
            "total_samples": len(self._history),
            "detection_rate": sum(detections) / len(detections),
            "mean_confidence": statistics.mean(confidences),
            "max_confidence": max(confidences),
            "min_confidence": min(confidences)
        }

    def reset(self) -> None:
        """Reset fusion engine state"""
        self._history.clear()
        self._confirmation_count = 0
