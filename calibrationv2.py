"""
Confidence Calibration for Contract Classifier.
Provides Platt scaling and Isotonic regression for calibrated confidence scores.
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

try:
    from sklearn.linear_model import LogisticRegression
    from sklearn.isotonic import IsotonicRegression
    from sklearn.metrics import brier_score_loss
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger("confidence_calibrator")


def calculate_ece(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    """Calculates Expected Calibration Error (ECE)."""
    bin_boundaries = np.linspace(0, 1, n_bins + 1)
    ece = 0.0

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        if i == n_bins - 1:
            in_bin = (y_prob >= bin_lower) & (y_prob <= bin_upper)
        else:
            in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper)

        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(y_true[in_bin])
            avg_confidence_in_bin = np.mean(y_prob[in_bin])
            ece += np.abs(avg_confidence_in_bin - accuracy_in_bin) * prop_in_bin

    return float(ece)


class ConfidenceCalibrator:
    """
    Calibrates raw scores (heuristics, LLM confidence, or similarity) to true probabilities.
    
    Supports:
      - 'platt': Sigmoid calibration via Logistic Regression (ideal for smaller datasets).
      - 'isotonic': Non-parametric isotonic regression (ideal for larger datasets, >= 1000 samples).
      - 'auto': Trains both and picks the method with the lowest Brier Score on validation data.
    """

    def __init__(self, method: str = "auto"):
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required. Install with: pip install scikit-learn")

        self.method = method
        self.calibrator = None
        self.is_fitted = False
        self.thresholds: Dict[str, float] = {
            "auto_accept_threshold": 0.90,
            "manual_review_threshold": 0.60
        }

    def _init_estimator(self, method: str):
        if method == "platt":
            # Direct Platt Scaling on 1D score: P(Y=1|s) = 1 / (1 + exp(-(As + B)))
            return LogisticRegression(solver="lbfgs", max_iter=1000)
        elif method == "isotonic":
            return IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
        else:
            raise ValueError(f"Unknown calibration method: {method}")

    def fit(self, scores: List[float], labels: List[int]) -> "ConfidenceCalibrator":
        """Fit directly from score and binary label lists."""
        X = np.array(scores, dtype=float)
        y = np.array(labels, dtype=int)

        if self.method == "auto":
            # Split train/val to compare Platt vs Isotonic objectively
            X_tr, X_val, y_tr, y_val = train_test_split(
                X, y, test_size=0.25, random_state=42, stratify=y
            )
            
            # 1. Platt
            platt = self._init_estimator("platt").fit(X_tr.reshape(-1, 1), y_tr)
            platt_probs = platt.predict_proba(X_val.reshape(-1, 1))[:, 1]
            platt_brier = brier_score_loss(y_val, platt_probs)

            # 2. Isotonic
            iso = self._init_estimator("isotonic").fit(X_tr, y_tr)
            iso_probs = iso.predict(X_val)
            iso_brier = brier_score_loss(y_val, iso_probs)

            if iso_brier < platt_brier:
                self.method = "isotonic"
                self.calibrator = self._init_estimator("isotonic").fit(X, y)
            else:
                self.method = "platt"
                self.calibrator = self._init_estimator("platt").fit(X.reshape(-1, 1), y)
        else:
            self.calibrator = self._init_estimator(self.method)
            if self.method == "platt":
                self.calibrator.fit(X.reshape(-1, 1), y)
            else:
                self.calibrator.fit(X, y)

        self.is_fitted = True
        return self

    def fit_from_json(
        self,
        json_path_or_data: Union[str, Path, List[Dict[str, Any]]],
        score_key: str = "raw_score",
        pred_key: str = "predicted_label",
        truth_key: str = "ground_truth_label",
        target_precision: float = 0.95
    ) -> "ConfidenceCalibrator":
        """
        Fits calibrator using raw JSON data by cross-referencing predicted and true labels.
        """
        if isinstance(json_path_or_data, (str, Path)):
            with open(json_path_or_data, "r", encoding="utf-8") as f:
                records = json.load(f)
        else:
            records = json_path_or_data

        scores: List[float] = []
        labels: List[int] = []

        for row in records:
            raw_s = row.get(score_key)
            pred = row.get(pred_key)
            truth = row.get(truth_key)

            if raw_s is None or pred is None or truth is None:
                continue

            scores.append(float(raw_s))
            # Binary target: 1 if prediction matches ground truth, else 0
            labels.append(1 if str(pred).strip().lower() == str(truth).strip().lower() else 0)

        if not scores:
            raise ValueError("No valid evaluation records found in the provided JSON data.")

        # Fit calibrator
        self.fit(scores, labels)

        # Optimize thresholds based on target precision
        self._calculate_thresholds(scores, labels, target_precision)
        return self

    def _calculate_thresholds(
        self, 
        scores: List[float], 
        labels: List[int], 
        target_precision: float
    ) -> None:
        """Derives cutoffs for straight-through automation vs manual review."""
        probs = self.predict_proba(scores)
        y = np.array(labels)

        auto_threshold = 0.95
        for th in np.linspace(0.50, 0.99, 50):
            accepted = probs >= th
            if np.sum(accepted) > 0:
                precision = np.mean(y[accepted])
                if precision >= target_precision:
                    auto_threshold = float(th)
                    break

        self.thresholds = {
            "auto_accept_threshold": round(auto_threshold, 3),
            "manual_review_threshold": 0.60
        }

    def predict_proba(self, scores: Union[float, List[float]]) -> np.ndarray:
        """Predict calibrated probabilities for a single score or list of scores."""
        if not self.is_fitted:
            raise ValueError("Calibrator not fitted. Call fit() or fit_from_json() first.")

        single_input = isinstance(scores, (int, float))
        scores_arr = np.array([scores] if single_input else scores, dtype=float)

        if self.method == "platt":
            probs = self.calibrator.predict_proba(scores_arr.reshape(-1, 1))[:, 1]
        else:
            probs = self.calibrator.predict(scores_arr)

        probs = np.clip(probs, 0.0, 1.0)
        return probs[0] if single_input else probs

    def calibrate_and_route(self, raw_score: float) -> Dict[str, Any]:
        """
        Calibrates the score and provides the routing action for downstream systems.
        """
        prob = float(self.predict_proba(raw_score))

        if prob >= self.thresholds["auto_accept_threshold"]:
            action = "AUTO_ACCEPT"
        elif prob >= self.thresholds["manual_review_threshold"]:
            action = "MANUAL_REVIEW"
        else:
            action = "REJECT"

        return {
            "raw_score": raw_score,
            "calibrated_confidence": round(prob, 4),
            "action": action
        }

    def save(self, path: Union[str, Path]) -> None:
        """Saves calibrator state, algorithm type, and thresholds."""
        with open(path, "wb") as f:
            pickle.dump({
                "method": self.method,
                "calibrator": self.calibrator,
                "is_fitted": self.is_fitted,
                "thresholds": self.thresholds
            }, f)

    @classmethod
    def load(cls, path: Union[str, Path]) -> "ConfidenceCalibrator":
        """Loads calibrator from disk."""
        with open(path, "rb") as f:
            data = pickle.load(f)

        instance = cls(method=data["method"])
        instance.calibrator = data["calibrator"]
        instance.is_fitted = data["is_fitted"]
        instance.thresholds = data.get("thresholds", {
            "auto_accept_threshold": 0.90,
            "manual_review_threshold": 0.60
        })
        return instance