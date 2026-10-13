"""Train a leakage-aware high-rating classifier on restaurant-level Gold data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.impute import SimpleImputer
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    PrecisionRecallDisplay,
    RocCurveDisplay,
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler


FEATURE_COLUMNS = [
    "cost_for_two",
    "location_name",
    "restaurant_type_name",
    "online_order_available",
    "table_booking_available",
    "cuisines",
]
TARGET_COLUMN = "is_high_rated"


def flatten_text(values):
    """Convert the single cuisine column to a one-dimensional text sequence."""
    flattened = values.to_numpy().ravel() if hasattr(values, "to_numpy") else values.ravel()
    return pd.Series(flattened).fillna("").astype(str).str.replace(",", " ", regex=False)


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                    ]
                ),
                ["cost_for_two"],
            ),
            (
                "categorical",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encode", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                [
                    "location_name",
                    "restaurant_type_name",
                    "online_order_available",
                    "table_booking_available",
                ],
            ),
            (
                "cuisine",
                Pipeline(
                    [
                        ("flatten", FunctionTransformer(flatten_text, validate=False)),
                        ("vectorize", TfidfVectorizer(ngram_range=(1, 1), min_df=3)),
                    ]
                ),
                ["cuisines"],
            ),
        ]
    )


def scores(y_true: pd.Series, probabilities, predictions) -> dict:
    return {
        "roc_auc": round(float(roc_auc_score(y_true, probabilities)), 4),
        "pr_auc": round(float(average_precision_score(y_true, probabilities)), 4),
        "accuracy": round(float(accuracy_score(y_true, predictions)), 4),
        "precision": round(float(precision_score(y_true, predictions, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, predictions, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, predictions, zero_division=0)), 4),
    }


def train(input_path: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    figures_dir = output_dir / "figures"
    figures_dir.mkdir(exist_ok=True)
    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)

    data = pd.read_csv(input_path)
    data[TARGET_COLUMN] = data[TARGET_COLUMN].astype(str).str.lower().eq("true")
    groups = data["restaurant_key"]
    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    train_index, test_index = next(splitter.split(data, data[TARGET_COLUMN], groups))
    train_data = data.iloc[train_index].copy()
    test_data = data.iloc[test_index].copy()
    x_train, y_train = train_data[FEATURE_COLUMNS], train_data[TARGET_COLUMN]
    x_test, y_test = test_data[FEATURE_COLUMNS], test_data[TARGET_COLUMN]

    candidates = {
        "logistic_regression": LogisticRegression(max_iter=2000, class_weight="balanced", random_state=42),
        "random_forest": RandomForestClassifier(
            n_estimators=120,
            max_depth=14,
            min_samples_leaf=3,
            class_weight="balanced_subsample",
            n_jobs=1,
            random_state=42,
        ),
    }
    results = {}
    trained = {}
    for name, estimator in candidates.items():
        pipeline = Pipeline([("preprocess", build_preprocessor()), ("model", estimator)])
        pipeline.fit(x_train, y_train)
        probabilities = pipeline.predict_proba(x_test)[:, 1]
        predictions = pipeline.predict(x_test)
        results[name] = scores(y_test, probabilities, predictions)
        trained[name] = pipeline

    best_name = max(results, key=lambda name: results[name]["pr_auc"])
    best_model = trained[best_name]
    best_probabilities = best_model.predict_proba(x_test)[:, 1]
    best_predictions = best_model.predict(x_test)
    joblib.dump(best_model, models_dir / "high_rating_classifier.joblib")

    importance = permutation_importance(
        best_model,
        x_test,
        y_test,
        scoring="average_precision",
        n_repeats=5,
        random_state=42,
        n_jobs=1,
    )
    importance_frame = pd.DataFrame(
        {
            "feature": FEATURE_COLUMNS,
            "mean_pr_auc_decrease": importance.importances_mean,
            "std_pr_auc_decrease": importance.importances_std,
        }
    ).sort_values("mean_pr_auc_decrease", ascending=False)
    importance_frame.to_csv(output_dir / "model_feature_importance.csv", index=False)

    plt.style.use("seaborn-v0_8-whitegrid")
    figure, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    RocCurveDisplay.from_predictions(y_test, best_probabilities, ax=axes[0])
    axes[0].set_title(f"ROC Curve: {best_name.replace('_', ' ').title()}")
    PrecisionRecallDisplay.from_predictions(y_test, best_probabilities, ax=axes[1])
    axes[1].set_title(f"Precision-Recall Curve: {best_name.replace('_', ' ').title()}")
    ConfusionMatrixDisplay.from_predictions(y_test, best_predictions, ax=axes[2], colorbar=False, cmap="Blues")
    axes[2].set_title("Test Set Confusion Matrix")
    figure.tight_layout()
    figure.savefig(figures_dir / "rating_model_evaluation.png", dpi=180, bbox_inches="tight")
    plt.close(figure)

    figure, axis = plt.subplots(figsize=(8, 4.5))
    importance_frame.sort_values("mean_pr_auc_decrease").plot.barh(
        x="feature", y="mean_pr_auc_decrease", xerr="std_pr_auc_decrease", ax=axis, legend=False, color="#4f46e5"
    )
    axis.set_title("Permutation Importance by PR-AUC Decrease")
    axis.set_xlabel("Decrease after feature permutation")
    axis.set_ylabel("")
    figure.tight_layout()
    figure.savefig(figures_dir / "rating_model_feature_importance.png", dpi=180, bbox_inches="tight")
    plt.close(figure)

    report = {
        "target_definition": "High observed rating: rating >= 4.0 and vote_count >= 20.",
        "feature_exclusions": [
            "vote_count is excluded because it is part of the target eligibility rule.",
            "restaurant name, URL, address, review text, and dish text are excluded to avoid identity or post-outcome leakage.",
        ],
        "train_rows": int(len(train_data)),
        "test_rows": int(len(test_data)),
        "positive_rate_train": round(float(y_train.mean()), 4),
        "positive_rate_test": round(float(y_test.mean()), 4),
        "selection_metric": "PR-AUC",
        "best_model": best_name,
        "metrics": results,
    }
    (output_dir / "rating_model_metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Train restaurant high-rating classifiers.")
    parser.add_argument("--input", type=Path, default=Path("data/gold/model_features.csv"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args()
    report = train(args.input, args.output_dir)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
