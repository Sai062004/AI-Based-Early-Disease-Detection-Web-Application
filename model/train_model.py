from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    precision_recall_fscore_support,
    top_k_accuracy_score,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

from inference import ARTIFACTS_DIR, humanize_token, normalize_token


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
TRAINING_DATA_PATH = DATA_DIR / "Training.csv"
DESCRIPTION_DATA_PATH = DATA_DIR / "symptom_Description.csv"
PRECAUTION_DATA_PATH = DATA_DIR / "symptom_precaution.csv"
RANDOM_SEED = 42


def normalize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    frame.columns = [normalize_token(column) for column in frame.columns]
    return frame


def load_training_data() -> tuple[pd.DataFrame, pd.Series]:
    raw_frame = pd.read_csv(TRAINING_DATA_PATH).dropna(axis=1, how="all")
    raw_frame = normalize_columns(raw_frame)
    raw_frame = raw_frame.loc[:, ~raw_frame.columns.str.contains("^unnamed")]
    raw_frame["prognosis"] = raw_frame["prognosis"].str.strip()
    features = raw_frame.drop(columns=["prognosis"])
    target = raw_frame["prognosis"]
    return features, target


def load_descriptions() -> dict[str, str]:
    description_frame = pd.read_csv(DESCRIPTION_DATA_PATH)
    description_frame["Disease"] = description_frame["Disease"].str.strip()
    return dict(zip(description_frame["Disease"], description_frame["description"]))


def load_precautions() -> dict[str, list[str]]:
    precaution_frame = pd.read_csv(PRECAUTION_DATA_PATH)
    precaution_frame["Disease"] = precaution_frame["Disease"].str.strip()
    precaution_map: dict[str, list[str]] = {}
    for _, row in precaution_frame.iterrows():
        precaution_map[row["Disease"]] = [
            str(row[column]).strip()
            for column in precaution_frame.columns[1:]
            if pd.notna(row[column]) and str(row[column]).strip()
        ]
    return precaution_map


def build_disease_profiles(features: pd.DataFrame, target: pd.Series) -> tuple[dict[str, dict[str, float]], dict[str, list[str]]]:
    frame = features.copy()
    frame["prognosis"] = target.values
    profile_frame = frame.groupby("prognosis").mean(numeric_only=True)

    disease_profiles: dict[str, dict[str, float]] = {}
    disease_symptoms: dict[str, list[str]] = {}
    for disease, row in profile_frame.iterrows():
        sorted_row = row.sort_values(ascending=False)
        disease_profiles[disease] = {symptom: round(float(score), 4) for symptom, score in row.items()}
        disease_symptoms[disease] = [symptom for symptom, score in sorted_row.items() if score > 0][:12]

    return disease_profiles, disease_symptoms


def mask_positive_symptoms(frame: pd.DataFrame, keep_low: float, keep_high: float, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    masked = frame.copy().to_numpy()

    for index in range(masked.shape[0]):
        positive_indices = np.where(masked[index] == 1)[0]
        if len(positive_indices) <= 2:
            continue
        keep_ratio = rng.uniform(keep_low, keep_high)
        keep_count = max(2, int(round(len(positive_indices) * keep_ratio)))
        keep_indices = rng.choice(positive_indices, size=keep_count, replace=False)
        masked[index, positive_indices] = 0
        masked[index, keep_indices] = 1

    return pd.DataFrame(masked, columns=frame.columns)


def tune_model(x_train: pd.DataFrame, y_train: np.ndarray, class_count: int) -> tuple[dict[str, int | None], list[dict[str, float]]]:
    x_subtrain, x_valid, y_subtrain, y_valid = train_test_split(
        x_train,
        y_train,
        test_size=0.18,
        random_state=RANDOM_SEED,
        stratify=y_train,
    )

    augmented_x = pd.concat(
        [
            x_subtrain,
            mask_positive_symptoms(x_subtrain, 0.45, 0.8, RANDOM_SEED + 1),
            mask_positive_symptoms(x_subtrain, 0.3, 0.65, RANDOM_SEED + 2),
        ],
        ignore_index=True,
    )
    augmented_y = np.concatenate([y_subtrain, y_subtrain, y_subtrain])
    validation_masked = mask_positive_symptoms(x_valid, 0.35, 0.7, RANDOM_SEED + 3)

    candidates = [
        {"n_estimators": 300, "max_depth": 12},
        {"n_estimators": 300, "max_depth": 16},
        {"n_estimators": 300, "max_depth": 20},
        {"n_estimators": 500, "max_depth": 16},
        {"n_estimators": 500, "max_depth": 20},
    ]

    trial_results: list[dict[str, float]] = []
    best_config = candidates[0]
    best_score = -1.0

    for candidate in candidates:
        model = RandomForestClassifier(
            n_estimators=candidate["n_estimators"],
            max_depth=candidate["max_depth"],
            random_state=RANDOM_SEED,
            max_features="sqrt",
            min_samples_leaf=1,
            n_jobs=1,
        )
        model.fit(augmented_x, augmented_y)
        probabilities = model.predict_proba(validation_masked)
        predictions = probabilities.argmax(axis=1)
        masked_accuracy = accuracy_score(y_valid, predictions)
        masked_top3 = top_k_accuracy_score(y_valid, probabilities, k=3, labels=range(class_count))
        score = (0.7 * masked_accuracy) + (0.3 * masked_top3)
        trial = {
            "n_estimators": candidate["n_estimators"],
            "max_depth": candidate["max_depth"],
            "maskedAccuracy": round(float(masked_accuracy), 4),
            "maskedTop3Accuracy": round(float(masked_top3), 4),
            "score": round(float(score), 4),
        }
        trial_results.append(trial)
        if score > best_score:
            best_score = score
            best_config = candidate

    return best_config, trial_results


def train_model() -> dict[str, object]:
    features, target = load_training_data()
    label_encoder = LabelEncoder()
    encoded_target = label_encoder.fit_transform(target)

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        encoded_target,
        test_size=0.2,
        random_state=RANDOM_SEED,
        stratify=encoded_target,
    )

    best_config, tuning_results = tune_model(x_train, y_train, len(label_encoder.classes_))

    augmented_x_train = pd.concat(
        [
            x_train,
            mask_positive_symptoms(x_train, 0.45, 0.8, RANDOM_SEED + 10),
            mask_positive_symptoms(x_train, 0.3, 0.65, RANDOM_SEED + 11),
        ],
        ignore_index=True,
    )
    augmented_y_train = np.concatenate([y_train, y_train, y_train])
    masked_x_test = mask_positive_symptoms(x_test, 0.35, 0.7, RANDOM_SEED + 12)

    model = RandomForestClassifier(
        n_estimators=best_config["n_estimators"],
        max_depth=best_config["max_depth"],
        random_state=RANDOM_SEED,
        max_features="sqrt",
        min_samples_leaf=1,
        n_jobs=1,
    )
    model.fit(augmented_x_train, augmented_y_train)

    exact_probabilities = model.predict_proba(x_test)
    exact_predictions = exact_probabilities.argmax(axis=1)
    masked_probabilities = model.predict_proba(masked_x_test)
    masked_predictions = masked_probabilities.argmax(axis=1)

    weighted_precision, weighted_recall, weighted_f1, _ = precision_recall_fscore_support(
        y_test,
        masked_predictions,
        average="weighted",
        zero_division=0,
    )

    disease_profiles, disease_symptoms = build_disease_profiles(features, target)

    return {
        "model": model,
        "label_encoder": label_encoder,
        "feature_names": features.columns.tolist(),
        "exact_accuracy": round(float(accuracy_score(y_test, exact_predictions)), 4),
        "masked_accuracy": round(float(accuracy_score(y_test, masked_predictions)), 4),
        "masked_top3_accuracy": round(
            float(top_k_accuracy_score(y_test, masked_probabilities, k=3, labels=range(len(label_encoder.classes_)))),
            4,
        ),
        "weighted_precision": round(float(weighted_precision), 4),
        "weighted_recall": round(float(weighted_recall), 4),
        "weighted_f1": round(float(weighted_f1), 4),
        "classification_report": classification_report(
            y_test,
            masked_predictions,
            target_names=label_encoder.classes_,
            output_dict=True,
            zero_division=0,
        ),
        "confusion_matrix": confusion_matrix(y_test, masked_predictions).tolist(),
        "disease_profiles": disease_profiles,
        "disease_symptoms": disease_symptoms,
        "tuning_results": tuning_results,
        "best_config": best_config,
    }


def save_artifacts(training_output: dict[str, object]) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    descriptions = load_descriptions()
    precautions = load_precautions()
    feature_names = training_output["feature_names"]
    symptom_display_map = {item: humanize_token(item) for item in feature_names}

    bundle = {
        "model": training_output["model"],
        "label_encoder": training_output["label_encoder"],
        "feature_names": feature_names,
    }
    joblib.dump(bundle, ARTIFACTS_DIR / "model_bundle.joblib")

    metrics = {
        "exactAccuracy": training_output["exact_accuracy"],
        "maskedAccuracy": training_output["masked_accuracy"],
        "maskedTop3Accuracy": training_output["masked_top3_accuracy"],
        "weightedPrecision": training_output["weighted_precision"],
        "weightedRecall": training_output["weighted_recall"],
        "weightedF1": training_output["weighted_f1"],
        "diseaseCount": len(training_output["label_encoder"].classes_),
        "symptomCount": len(feature_names),
        "bestConfig": training_output["best_config"],
    }

    metadata = {
        "metrics": metrics,
        "descriptions": descriptions,
        "precautions": precautions,
        "disease_profiles": training_output["disease_profiles"],
        "disease_symptoms": training_output["disease_symptoms"],
        "symptom_display_map": symptom_display_map,
    }

    with (ARTIFACTS_DIR / "metadata.json").open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, indent=2)

    with (ARTIFACTS_DIR / "metrics.json").open("w", encoding="utf-8") as metrics_file:
        json.dump(
            {
                **metrics,
                "tuningResults": training_output["tuning_results"],
                "classificationReport": training_output["classification_report"],
                "confusionMatrix": training_output["confusion_matrix"],
                "confusionMatrixLabels": training_output["label_encoder"].classes_.tolist(),
            },
            metrics_file,
            indent=2,
        )


def main() -> None:
    training_output = train_model()
    save_artifacts(training_output)
    print(
        json.dumps(
            {
                "exact_accuracy": training_output["exact_accuracy"],
                "masked_accuracy": training_output["masked_accuracy"],
                "masked_top3_accuracy": training_output["masked_top3_accuracy"],
                "best_config": training_output["best_config"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
