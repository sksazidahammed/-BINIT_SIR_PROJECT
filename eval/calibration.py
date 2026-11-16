# Calibration module: temperature scaling, two-threshold decision policy, and ECE calculation.
# Product Rule: Two thresholds give three output states (indicated / inconclusive / not indicated).
from __future__ import annotations
from typing import Any, Dict, List, Tuple
import numpy as np
from scipy.optimize import minimize

def sigmoid(z: np.ndarray) -> np.ndarray:
    """Numerically stable sigmoid function."""
    return np.where(z >= 0, 1.0 / (1.0 + np.exp(-z)), np.exp(z) / (1.0 + np.exp(z)))

def brier_score(y_true: np.ndarray, y_prob: np.ndarray) -> float:
    """Compute Brier calibration score (mean squared error of probability predictions)."""
    return float(np.mean((y_prob - y_true) ** 2))

def expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Compute Expected Calibration Error (ECE) across probability bins."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(y_true)

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper if i < n_bins - 1 else y_prob <= bin_upper)
        prop_in_bin = np.mean(in_bin)

        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(y_true[in_bin])
            avg_confidence_in_bin = np.mean(y_prob[in_bin])
            ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin

    return float(ece)

class TemperatureScaler:
    """
    Fits a single temperature parameter T > 0 on logits z to minimize cross-entropy loss.
    Fitted on calibration split, then frozen for all subsequent test inferences.
    """
    def __init__(self, temperature: float = 1.0):
        self.temperature = float(temperature)

    def fit(self, logits: np.ndarray, y_true: np.ndarray) -> TemperatureScaler:
        """Fit temperature T on calibration split."""
        logits = np.asarray(logits, dtype=np.float64)
        y_true = np.asarray(y_true, dtype=np.float64)

        def nll(t_val):
            t = t_val[0]
            if t <= 0:
                return 1e9
            scaled_logits = logits / t
            probs = sigmoid(scaled_logits)
            eps = 1e-12
            probs = np.clip(probs, eps, 1.0 - eps)
            loss = -np.mean(y_true * np.log(probs) + (1.0 - y_true) * np.log(1.0 - probs))
            return loss

        res = minimize(nll, [1.0], method="Nelder-Mead", bounds=[(0.05, 20.0)])
        self.temperature = float(res.x[0])
        return self

    def predict_proba(self, logits: np.ndarray) -> np.ndarray:
        """Calibrate logits using the frozen temperature parameter."""
        scaled = np.asarray(logits, dtype=np.float64) / self.temperature
        return sigmoid(scaled)

class TwoThresholdClassifier:
    """
    Implements the two-threshold decision rule producing three states:
      - prob >= theta_high -> "synthetic indicated"
      - theta_low < prob < theta_high -> "inconclusive"
      - prob <= theta_low -> "synthetic not indicated"
    Thresholds are selected on the calibration split and then frozen.
    """
    def __init__(self, theta_low: float = 0.35, theta_high: float = 0.65):
        if not (0.0 <= theta_low < theta_high <= 1.0):
            raise ValueError(f"Invalid thresholds: theta_low={theta_low}, theta_high={theta_high}")
        self.theta_low = float(theta_low)
        self.theta_high = float(theta_high)

    def classify(self, prob: float) -> str:
        """Classify a single calibrated probability into one of three states."""
        prob = float(prob)
        if prob >= self.theta_high:
            return "synthetic indicated"
        elif prob <= self.theta_low:
            return "synthetic not indicated"
        else:
            return "inconclusive"

    def evaluate_coverage(self, probs: np.ndarray) -> Dict[str, float]:
        """Compute proportion of decisions made vs abstained (inconclusive)."""
        probs = np.asarray(probs)
        decided = (probs >= self.theta_high) | (probs <= self.theta_low)
        coverage = float(np.mean(decided))
        abstention = 1.0 - coverage
        return {
            "coverage": round(coverage, 4),
            "abstention_rate": round(abstention, 4),
            "theta_low": self.theta_low,
            "theta_high": self.theta_high
        }
