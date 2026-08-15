"""
ml_core.py
----------
All ML logic: dataset validation, training, prediction helpers.
Called only by app.py. Never imports Flask.
"""

import datetime
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import joblib

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")
VIZ_DIR   = os.path.join(BASE_DIR, "static", "visualizations")
DATA_DIR  = os.path.join(BASE_DIR, "uploads")

MODEL_PATH   = os.path.join(MODEL_DIR, "house_price_model.pkl")
METRICS_PATH = os.path.join(MODEL_DIR, "metrics.json")
STATUS_PATH  = os.path.join(MODEL_DIR, "status.json")
VIZ_PATH     = os.path.join(VIZ_DIR,  "actual_vs_predicted.png")

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(VIZ_DIR,   exist_ok=True)
os.makedirs(DATA_DIR,  exist_ok=True)

REQUIRED_COLUMNS = {"area_sqft", "bedrooms", "bathrooms", "location", "price"}


# ══════════════════════════════════════════════════════════════════════════════
#  Dataset helpers
# ══════════════════════════════════════════════════════════════════════════════

def validate_csv(filepath: str) -> pd.DataFrame:
    """
    Load and validate a CSV file.
    Returns a clean DataFrame or raises ValueError with a human-readable message.
    """
    if not os.path.isfile(filepath):
        raise ValueError("File not found on the server.")

    try:
        df = pd.read_csv(filepath)
    except Exception as exc:
        raise ValueError(f"Could not parse CSV: {exc}")

    if df.empty:
        raise ValueError("The CSV file is empty.")

    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        raise ValueError(
            f"Missing required columns: {sorted(missing_cols)}. "
            f"Required: {sorted(REQUIRED_COLUMNS)}."
        )

    # Numeric columns must be coercible (NaN is acceptable — imputer handles it)
    for col in ("area_sqft", "bedrooms", "bathrooms", "price"):
        # Count values that are non-null AND cannot be coerced to numeric
        original_na  = df[col].isna()
        coerced      = pd.to_numeric(df[col], errors="coerce")
        newly_na     = coerced.isna() & ~original_na   # was non-null but failed coerce
        bad          = int(newly_na.sum())
        if bad > 0:
            raise ValueError(
                f"Column '{col}' contains {bad} non-numeric value(s) "
                f"(NaN/missing values are allowed and will be imputed)."
            )

    # Price must be positive where it exists
    prices = pd.to_numeric(df["price"], errors="coerce")
    valid_prices = prices.dropna()
    if len(valid_prices) > 0 and (valid_prices <= 0).any():
        raise ValueError("Column 'price' must contain only positive values.")

    return df


def get_dataset_info(filepath: str) -> dict:
    """
    Return metadata about the current active dataset CSV.
    All values come from the actual file — nothing is hardcoded.
    """
    df = validate_csv(filepath)

    missing_per_col = df.isnull().sum()
    missing_detail  = {
        col: int(missing_per_col[col])
        for col in df.columns
        if missing_per_col[col] > 0
    }

    return {
        "rows":           int(len(df)),
        "columns":        int(len(df.columns)),
        "features":       ["area_sqft", "bedrooms", "bathrooms", "location"],
        "target":         "price",
        "locations":      sorted(df["location"].dropna().unique().tolist()),
        "missing_values": int(df.isnull().sum().sum()),
        "missing_detail": missing_detail,
        "price_min":      float(df["price"].min()),
        "price_max":      float(df["price"].max()),
        "price_mean":     float(df["price"].mean()),
    }


# ══════════════════════════════════════════════════════════════════════════════
#  Status helpers
# ══════════════════════════════════════════════════════════════════════════════

def load_status() -> dict:
    """Return the persisted model status, or a default 'not trained' dict."""
    if os.path.isfile(STATUS_PATH):
        try:
            with open(STATUS_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "trained":       False,
        "model":         "Random Forest Regressor",
        "status":        "Not Trained",
        "dataset_file":  None,
        "trained_at":    None,
        "train_records": None,
        "test_records":  None,
    }


def _save_status(status: dict) -> None:
    with open(STATUS_PATH, "w") as f:
        json.dump(status, f, indent=2)


def load_metrics() -> dict:
    """Return saved metrics or empty dict."""
    if os.path.isfile(METRICS_PATH):
        try:
            with open(METRICS_PATH) as f:
                return json.load(f)
        except Exception:
            pass
    return {}


# ══════════════════════════════════════════════════════════════════════════════
#  Training
# ══════════════════════════════════════════════════════════════════════════════

def train_model(filepath: str) -> dict:
    """
    Full training pipeline:
      1. Validate & load CSV
      2. Preprocess (impute → scale → one-hot)
      3. Train RandomForestRegressor (80 / 20 split)
      4. Compute R², MAE, RMSE
      5. Save pipeline (joblib), metrics (json), status (json), plot (png)
    Returns the metrics dict.
    Raises ValueError on bad data.
    """
    df = validate_csv(filepath)

    # Drop rows where target or the most critical feature is missing
    df = df.dropna(subset=["price", "area_sqft"]).copy()

    if len(df) < 20:
        raise ValueError(
            f"Only {len(df)} valid rows after removing nulls — "
            "need at least 20 to train."
        )

    X = df[["area_sqft", "bedrooms", "bathrooms", "location"]]
    y = df["price"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )

    # ── Preprocessor ──────────────────────────────────────────────────────────
    num_features = ["area_sqft", "bedrooms", "bathrooms"]
    cat_features = ["location"]

    num_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler",  StandardScaler()),
    ])
    cat_pipe = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot",  OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])
    preprocessor = ColumnTransformer([
        ("num", num_pipe, num_features),
        ("cat", cat_pipe, cat_features),
    ])

    # ── Full pipeline ──────────────────────────────────────────────────────────
    pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("regressor",    RandomForestRegressor(
            n_estimators=200,
            max_depth=None,
            min_samples_split=2,
            random_state=42,
            n_jobs=-1,
        )),
    ])

    pipeline.fit(X_train, y_train)

    # ── Evaluate ───────────────────────────────────────────────────────────────
    y_pred = pipeline.predict(X_test)

    r2   = float(r2_score(y_test, y_pred))
    mae  = float(mean_absolute_error(y_test, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))

    # ── Save pipeline ──────────────────────────────────────────────────────────
    joblib.dump(pipeline, MODEL_PATH)

    # ── Save metrics ───────────────────────────────────────────────────────────
    metrics = {
        "model":           "Random Forest Regressor",
        "r2_score":        round(r2,   6),
        "mae":             round(mae,  2),
        "rmse":            round(rmse, 2),
        "dataset_records": int(len(df)),
        "train_size":      int(len(X_train)),
        "test_size":       int(len(X_test)),
        "locations":       sorted(df["location"].dropna().unique().tolist()),
        "trained_at":      datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)

    # ── Save status ────────────────────────────────────────────────────────────
    status = {
        "trained":       True,
        "model":         "Random Forest Regressor",
        "status":        "Trained",
        "dataset_file":  os.path.basename(filepath),
        "trained_at":    metrics["trained_at"],
        "train_records": int(len(X_train)),
        "test_records":  int(len(X_test)),
    }
    _save_status(status)

    # ── Generate visualization ─────────────────────────────────────────────────
    _generate_plot(y_test, y_pred, metrics)

    return metrics


def _generate_plot(y_test: pd.Series, y_pred: np.ndarray, metrics: dict) -> None:
    """Actual vs Predicted scatter plot — saved to static/visualizations/."""
    y_t = np.array(y_test)  / 1_000_000
    y_p = np.array(y_pred)  / 1_000_000

    fig, ax = plt.subplots(figsize=(9, 7))

    ax.scatter(
        y_t, y_p,
        alpha=0.55, color="#1e3a8a", edgecolor="white",
        linewidth=0.4, s=65, label="Predictions", zorder=3,
    )

    lo = min(y_t.min(), y_p.min()) * 0.95
    hi = max(y_t.max(), y_p.max()) * 1.05
    ax.plot([lo, hi], [lo, hi], "r--", lw=1.8, label="Perfect fit", zorder=4)

    # ±10 % band
    ax.fill_between(
        [lo, hi], [lo * 0.90, hi * 0.90], [lo * 1.10, hi * 1.10],
        alpha=0.10, color="#10b981", label="±10% band",
    )

    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_xlabel("Actual Price (Millions PKR)",    fontsize=12, labelpad=8)
    ax.set_ylabel("Predicted Price (Millions PKR)", fontsize=12, labelpad=8)
    ax.set_title(
        "Actual vs Predicted House Prices — Test Set",
        fontsize=14, fontweight="bold", pad=14,
    )

    stats = (
        f"R² = {metrics['r2_score']:.4f}\n"
        f"MAE  = PKR {metrics['mae']/1e6:.2f} M\n"
        f"RMSE = PKR {metrics['rmse']/1e6:.2f} M\n"
        f"n (test) = {metrics['test_size']}"
    )
    ax.text(
        0.04, 0.96, stats,
        transform=ax.transAxes, fontsize=9.5,
        verticalalignment="top",
        bbox=dict(boxstyle="round,pad=0.5", facecolor="white",
                  edgecolor="#d1d5db", alpha=0.92),
    )

    ax.legend(fontsize=10, loc="lower right")
    ax.grid(True, linestyle="--", alpha=0.40)
    ax.set_facecolor("#f9fafb")
    fig.patch.set_facecolor("#ffffff")
    fig.tight_layout()

    fig.savefig(VIZ_PATH, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ══════════════════════════════════════════════════════════════════════════════
#  Prediction
# ══════════════════════════════════════════════════════════════════════════════

def predict_price(pipeline, area_sqft: float, bedrooms: float,
                  bathrooms: float, location: str) -> float:
    """
    Run inference on the loaded pipeline.
    Returns predicted price as a float.
    """
    input_df = pd.DataFrame([{
        "area_sqft": area_sqft,
        "bedrooms":  bedrooms,
        "bathrooms": bathrooms,
        "location":  location,
    }])
    return float(pipeline.predict(input_df)[0])
