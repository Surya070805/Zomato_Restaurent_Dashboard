"""Train the high-rating classifier with MLflow experiment tracking.

Same model contract as ``src/train_rating_model.py`` (grouped split by restaurant key,
leakage-aware features, PR-AUC selection), but each candidate run is logged to MLflow so
experiments can be compared.

Works in two environments:

* **Databricks** - MLflow is preinstalled. Pass ``--feature-table main.zomato.model_features``
  to read from a Delta table; runs appear under the ``zomato_rating_model`` experiment.
* **Local** - if MLflow is not installed the script still trains and writes the same
  metrics/figures to ``reports/``, printing what would have been logged. This keeps the
  script runnable without a tracking server.

Usage:
    python src/train_rating_model_mlflow.py --input data/gold/model_features.csv
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.inspection import permutation_importance
from sklearn.model_selection import GroupShuffleSplit
from sklearn.pipeline import Pipeline

from train_rating_model import FEATURE_COLUMNS, TARGET_COLUMN, build_preprocessor

EXPERIMENT_NAME = "zomato_rating_model"

try:  # MLflow is present on Databricks ML runtimes; optional elsewhere.
    import mlflow
    import mlflow.sklearn

    MLFLOW_AVAILABLE = True
except Exception:  # pragma: no cover - depends on environment
    mlflow = None
    MLFLOW_AVAILABLE = False


def load_data(input_path: Path | None, feature_table: str | None) -> pd.DataFrame:
    """Read the restaurant-grain feature table from Delta (Databricks) or CSV (local)."""
    if feature_table:
        try:
            from pyspark.sql import SparkSession

            spark = SparkSession.builder.getOrCreate()
            return spark.table(feature_table).toPandas()
        except Exception as error:  # pragma: no cover - Databricks only
            print(f"Delta read failed ({error}); falling back to CSV.")
    if input_path is None:
        raise ValueError("Provide either --input or --feature-table.")
    return pd.read_csv(input_path)


def candidate_models() -> dict:
    return {
        "logistic_regression": LogisticRegression(
            max_iter=2000, class_weight="balanced", random_state=42
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=120,
            max_depth=14,
            min_samples_leaf=3,
            class_weight="balanced_subsample",
            n_jobs=1,
            random_state=42,
        ),
    }


def evaluate(model: Pipeline, x_test: pd.DataFrame, y_test: pd.Series) -> dict:
    probabilities = model.predict_proba(x_test)[:, 1]
    predictions = model.predict(x_test)
    return {
        "roc_auc": float(roc_auc_score(y_test, probabilities)),
        "pr_auc": float(average_precision_score(y_test, probabilities)),
        "accuracy": float(accuracy_score(y_test, predictions)),
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, zero_division=0)),
        "f1": float(f1_score(y_test, predictions, zero_division=0)),
    }


def train(input_path: Path | None, feature_table: str | None, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = output_dir / "mlflow_artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    data = load_data(input_path, feature_table)
    data[TARGET_COLUMN] = data[TARGET_COLUMN].astype(str).str.lower().eq("true")

    splitter = GroupShuffleSplit(n_splits=1, test_size=0.25, random_state=42)
    train_index, test_index = next(
        splitter.split(data, data[TARGET_COLUMN], data["restaurant_key"])
    )
    train_data = data.iloc[train_index]
    test_data = data.iloc[test_index]
    x_train, y_train = train_data[FEATURE_COLUMNS], train_data[TARGET_COLUMN]
    x_test, y_test = test_data[FEATURE_COLUMNS], test_data[TARGET_COLUMN]

    if MLFLOW_AVAILABLE:
        mlflow.set_experiment(EXPERIMENT_NAME)
    else:
        print("MLflow not installed: training without a tracking server.")

    results: dict[str, dict] = {}
    importance_frames: dict[str, pd.DataFrame] = {}
    fitted: dict[str, Pipeline] = {}

    for name, estimator in candidate_models().items():
        run_context = (
            mlflow.start_run(run_name=name) if MLFLOW_AVAILABLE else _null_context()
        )
        with run_context:
            pipeline = Pipeline([("preprocess", build_preprocessor()), ("model", estimator)])
            pipeline.fit(x_train, y_train)
            fitted[name] = pipeline
            metrics = evaluate(pipeline, x_test, y_test)
            results[name] = {key: round(value, 4) for key, value in metrics.items()}

            importance = permutation_importance(
                pipeline,
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
            importance_frames[name] = importance_frame
            importance_path = artifacts_dir / f"importance_{name}.csv"
            importance_frame.to_csv(importance_path, index=False)

            if MLFLOW_AVAILABLE:
                mlflow.log_params(
                    {
                        "model_family": name,
                        "features": ",".join(FEATURE_COLUMNS),
                        "target": "rating >= 4.0 and votes >= 20",
                        "split": "GroupShuffleSplit by restaurant_key, test_size=0.25",
                        "train_rows": len(train_data),
                        "test_rows": len(test_data),
                    }
                )
                if name == "random_forest":
                    mlflow.log_params(
                        {
                            "n_estimators": estimator.n_estimators,
                            "max_depth": estimator.max_depth,
                            "min_samples_leaf": estimator.min_samples_leaf,
                        }
                    )
                mlflow.log_metrics(results[name])
                mlflow.log_artifact(str(importance_path))
                mlflow.sklearn.log_model(pipeline, artifact_path="model")
                print(f"[mlflow] logged run '{name}' with metrics {results[name]}")
            else:
                print(f"[local] {name} metrics {results[name]}")

    best_name = max(results, key=lambda key: results[key]["pr_auc"])
    summary = {
        "target_definition": "High observed rating: rating >= 4.0 and vote_count >= 20.",
        "selection_metric": "PR-AUC",
        "best_model": best_name,
        "train_rows": int(len(train_data)),
        "test_rows": int(len(test_data)),
        "mlflow_available": MLFLOW_AVAILABLE,
        "experiment": EXPERIMENT_NAME if MLFLOW_AVAILABLE else None,
        "metrics": results,
    }

    models_dir = Path("models")
    models_dir.mkdir(exist_ok=True)
    joblib.dump(fitted[best_name], models_dir / "high_rating_classifier.joblib")

    importance_frames[best_name].to_csv(output_dir / "model_feature_importance.csv", index=False)
    (output_dir / "mlflow_run_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return summary


class _null_context:
    """No-op context manager used when MLflow is unavailable."""

    def __enter__(self):
        return None

    def __exit__(self, *exc_info):
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Train rating models with MLflow tracking.")
    parser.add_argument("--input", type=Path, default=Path("data/gold/model_features.csv"))
    parser.add_argument("--feature-table", type=str, default=None)
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args()
    summary = train(args.input, args.feature_table, args.output_dir)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
