from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Iterable

import joblib
import numpy as np
import pandas as pd


ARTIFACTS_DIR = Path(__file__).resolve().parent / "artifacts"
MODEL_BUNDLE_PATH = ARTIFACTS_DIR / "model_bundle.joblib"
METADATA_PATH = ARTIFACTS_DIR / "metadata.json"


def normalize_token(value: str) -> str:
    cleaned = value.strip().lower()
    cleaned = cleaned.replace("-", " ")
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.replace(" ", "_")
    return cleaned


def humanize_token(value: str) -> str:
    label = value.replace("_", " ").replace("(", "").replace(")", "")
    label = re.sub(r"\s+", " ", label).strip()
    return label.title()


class LifeLensPredictor:
    def __init__(self) -> None:
        if not MODEL_BUNDLE_PATH.exists():
            raise FileNotFoundError(
                "Model artifact is missing. Run model/train_model.py before using prediction."
            )
        self.bundle = joblib.load(MODEL_BUNDLE_PATH)
        with METADATA_PATH.open("r", encoding="utf-8") as metadata_file:
            self.metadata = json.load(metadata_file)

        self.model = self.bundle["model"]
        self.label_encoder = self.bundle["label_encoder"]
        self.feature_names = self.bundle["feature_names"]
        self.feature_lookup = {name: index for index, name in enumerate(self.feature_names)}
        self.class_names = list(self.label_encoder.classes_)
        self.symptom_display_map = self.metadata["symptom_display_map"]
        self.description_map = self.metadata["descriptions"]
        self.precaution_map = self.metadata["precautions"]
        self.disease_symptom_map = self.metadata["disease_symptoms"]
        self.disease_profiles = self.metadata["disease_profiles"]
        self.model_metrics = self.metadata["metrics"]
        self.symptom_aliases = self._build_aliases(self.feature_names)

    @staticmethod
    def _build_aliases(feature_names: Iterable[str]) -> dict[str, str]:
        aliases: dict[str, str] = {}
        for name in feature_names:
            pretty = humanize_token(name)
            alias_candidates = {
                name,
                normalize_token(name),
                normalize_token(pretty),
                normalize_token(pretty.replace("And", "&")),
            }
            alias_candidates |= {candidate.replace("_", "") for candidate in alias_candidates}
            for candidate in alias_candidates:
                aliases[candidate] = name
        return aliases

    def resolve_symptoms(self, symptoms: Iterable[str]) -> tuple[list[str], list[str]]:
        resolved: list[str] = []
        unresolved: list[str] = []
        seen: set[str] = set()

        for symptom in symptoms:
            normalized = normalize_token(symptom)
            compact = normalized.replace("_", "")
            match = self.symptom_aliases.get(normalized) or self.symptom_aliases.get(compact)
            if match and match not in seen:
                resolved.append(match)
                seen.add(match)
            elif symptom.strip():
                unresolved.append(symptom.strip())

        return resolved, unresolved

    def build_feature_vector(self, symptoms: Iterable[str]) -> pd.DataFrame:
        payload = {feature: 0 for feature in self.feature_names}
        for symptom in symptoms:
            payload[symptom] = 1
        return pd.DataFrame([payload], columns=self.feature_names)

    def symptom_suggestions(self, disease_name: str, selected_symptoms: Iterable[str]) -> list[str]:
        known = set(selected_symptoms)
        ranked = self.disease_symptom_map.get(disease_name, [])
        suggestions = [item for item in ranked if item not in known]
        return [self.symptom_display_map[item] for item in suggestions[:5]]

    def hybrid_score(self, disease_name: str, model_probability: float, selected_symptoms: list[str]) -> tuple[float, float, float]:
        profile = self.disease_profiles.get(disease_name, {})
        if not selected_symptoms:
            return model_probability, 0.0, 0.0

        symptom_values = [float(profile.get(symptom, 0.0)) for symptom in selected_symptoms]
        coverage = sum(symptom_values) / len(symptom_values)
        support = sum(1 for score in symptom_values if score >= 0.5) / len(symptom_values)
        anchor = max(symptom_values) if symptom_values else 0.0
        similarity_score = 0.55 * coverage + 0.30 * support + 0.15 * anchor

        model_weight = 0.35 if len(selected_symptoms) <= 5 else 0.45
        hybrid = (model_weight * model_probability) + ((1 - model_weight) * similarity_score)
        return hybrid, coverage, support

    def predict(self, symptoms: Iterable[str], top_k: int = 3) -> dict[str, Any]:
        resolved, unresolved = self.resolve_symptoms(symptoms)
        if not resolved:
            raise ValueError("Please provide at least one valid symptom.")

        feature_vector = self.build_feature_vector(resolved)
        probabilities = self.model.predict_proba(feature_vector)[0]
        model_probability_map = {
            self.class_names[index]: float(probability)
            for index, probability in enumerate(probabilities)
        }

        ranked_predictions: list[dict[str, Any]] = []
        for disease_name in self.class_names:
            hybrid, coverage, support = self.hybrid_score(
                disease_name,
                model_probability_map.get(disease_name, 0.0),
                resolved,
            )
            ranked_predictions.append(
                {
                    "disease": disease_name,
                    "hybrid": hybrid,
                    "coverage": coverage,
                    "support": support,
                    "modelProbability": model_probability_map.get(disease_name, 0.0),
                }
            )

        ranked_predictions.sort(key=lambda item: item["hybrid"], reverse=True)
        top_predictions: list[dict[str, Any]] = []
        for item in ranked_predictions[:top_k]:
            confidence = round(item["hybrid"] * 100, 2)
            disease_name = item["disease"]
            top_predictions.append(
                {
                    "disease": disease_name,
                    "confidence": confidence,
                    "riskLevel": self._risk_level(item["hybrid"]),
                    "description": self.description_map.get(
                        disease_name, "No disease summary is available."
                    ),
                    "precautions": self.precaution_map.get(disease_name, []),
                    "suggestedSymptoms": self.symptom_suggestions(disease_name, resolved),
                    "symptomCoverage": round(item["coverage"] * 100, 2),
                    "symptomSupport": round(item["support"] * 100, 2),
                    "modelProbability": round(item["modelProbability"] * 100, 2),
                }
            )

        primary = top_predictions[0]
        return {
            "predictedDisease": primary["disease"],
            "confidence": primary["confidence"],
            "riskLevel": primary["riskLevel"],
            "description": primary["description"],
            "precautions": primary["precautions"],
            "topPredictions": top_predictions,
            "selectedSymptoms": [self.symptom_display_map[item] for item in resolved],
            "unknownSymptoms": unresolved,
            "suggestedSymptoms": primary["suggestedSymptoms"],
            "modelMetrics": self.model_metrics,
        }

    @staticmethod
    def _risk_level(score: float) -> str:
        if score >= 0.75:
            return "High"
        if score >= 0.45:
            return "Medium"
        return "Low"

    def get_catalog(self) -> dict[str, Any]:
        return {
            "symptoms": [
                {"value": item, "label": self.symptom_display_map[item]}
                for item in self.feature_names
            ],
            "metrics": self.model_metrics,
        }
