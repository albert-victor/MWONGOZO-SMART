from __future__ import annotations

from dataclasses import dataclass
from math import exp
from typing import Any


@dataclass(slots=True)
class FeatureVector:
    points_margin: float
    subject_fit: float
    competition_tier: float
    region_match: float
    capacity_factor: float = 0.0


class RuleBoostedRankingModel:
    """A lightweight, dependency-free probability model.

    This is intentionally simple so the engine stays usable without a
    historical training set. It can later be replaced by sklearn or
    LightGBM-backed estimation if real admissions data becomes available.
    """

    def __init__(self) -> None:
        # Simple weights that can later be replaced by a trained model.
        self.weights = {
            "bias": -0.8,
            "points_margin": 0.55,
            "subject_fit": 1.1,
            "competition_tier": -0.35,
            "region_match": 0.25,
            "capacity_factor": 0.12,
        }

    def predict_probability(self, features: FeatureVector | dict[str, Any]) -> float:
        # Convert features to a logistic score between 0 and 1.
        if isinstance(features, dict):
            features = FeatureVector(
                points_margin=float(features.get("points_margin", 0.0)),
                subject_fit=float(features.get("subject_fit", 0.0)),
                competition_tier=float(features.get("competition_tier", 0.0)),
                region_match=float(features.get("region_match", 0.0)),
                capacity_factor=float(features.get("capacity_factor", 0.0)),
            )
        score = (
            self.weights["bias"]
            + self.weights["points_margin"] * features.points_margin
            + self.weights["subject_fit"] * features.subject_fit
            + self.weights["competition_tier"] * features.competition_tier
            + self.weights["region_match"] * features.region_match
            + self.weights["capacity_factor"] * features.capacity_factor
        )
        return 1.0 / (1.0 + exp(-score))
