"""
app.py
------
Flask application for the House Price Predictor.
Two pages:  /          → Prediction (index.html)
            /dashboard → ML Dashboard (dashboard.html)

API endpoints:
  POST /api/upload-dataset
  POST /api/train
  POST /api/predict
  GET  /api/model-status
  GET  /api/dataset-info
  GET  /api/metrics
  GET  /visualization
"""

import json
import logging
import os
import uuid

import joblib
from flask import (Flask, jsonify, redirect, render_template,
                   request, send_from_directory, url_for)
from werkzeug.utils import secure_filename

import ml_core

# ── App setup ──────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["SECRET_KEY"]         = os.environ.get("SECRET_KEY", "houseprice-dev-secret")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024   # 16 MB upload limit

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("HousePriceApp")

# ── Persistence file for active dataset path ───────────────────────────────────
# Survives Flask restarts — stores the absolute path of the most recently
# uploaded and validated CSV so /api/dataset-info and /api/train always
# use the correct file after a restart.
ACTIVE_DATASET_FILE = os.path.join(ml_core.MODEL_DIR, "active_dataset.json")


def _save_active_csv(path: str) -> None:
    """Persist active CSV path to disk."""
    with open(ACTIVE_DATASET_FILE, "w") as f:
        json.dump({"active_csv_path": path}, f)


def _load_active_csv():
    """
    Return the persisted active CSV path if it still exists on disk.
    Falls back to the default house_data.csv if present.
    Returns None if neither is found.
    """
    # 1. Try the persisted upload path
    if os.path.isfile(ACTIVE_DATASET_FILE):
        try:
            with open(ACTIVE_DATASET_FILE) as f:
                data = json.load(f)
            path = data.get("active_csv_path", "")
            if path and os.path.isfile(path):
                return path
            logger.warning("Persisted CSV path no longer exists: %s", path)
        except Exception as exc:
            logger.warning("Could not read active_dataset.json: %s", exc)

    # 2. Fall back to default dataset
    default = os.path.join(BASE_DIR, "house_data.csv")
    if os.path.isfile(default):
        logger.info("Using default dataset: house_data.csv")
        return default

    return None


# ── Runtime state ──────────────────────────────────────────────────────────────
_pipeline        = None   # sklearn Pipeline — loaded at startup, refreshed after training
_active_csv_path = None   # absolute path to the active CSV — persisted across restarts


def _load_pipeline_from_disk():
    """Load the saved Joblib pipeline. Sets _pipeline to None on failure."""
    global _pipeline
    if os.path.isfile(ml_core.MODEL_PATH):
        try:
            _pipeline = joblib.load(ml_core.MODEL_PATH)
            logger.info("Pipeline loaded from disk.")
        except Exception as exc:
            logger.error("Failed to load pipeline: %s", exc)
            _pipeline = None
    else:
        logger.warning("No saved model found. Train via the dashboard first.")
        _pipeline = None


# ── Startup initialisation ─────────────────────────────────────────────────────
_load_pipeline_from_disk()

_active_csv_path = _load_active_csv()
if _active_csv_path:
    logger.info("Active dataset: %s", _active_csv_path)
else:
    logger.warning("No active dataset found. Upload a CSV to get started.")


# ── Page routes ────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Page 1 — Prediction."""
    status  = ml_core.load_status()
    metrics = ml_core.load_metrics()
    locations = metrics.get("locations", [])
    return render_template(
        "index.html",
        status=status,
        locations=locations,
    )


@app.route("/dashboard")
def dashboard():
    """Page 2 — ML Dashboard."""
    status  = ml_core.load_status()
    metrics = ml_core.load_metrics()

    # Dataset info (if a CSV is active)
    dataset_info = None
    if _active_csv_path and os.path.isfile(_active_csv_path):
        try:
            dataset_info = ml_core.get_dataset_info(_active_csv_path)
        except Exception:
            dataset_info = None

    viz_exists = os.path.isfile(ml_core.VIZ_PATH)

    return render_template(
        "dashboard.html",
        status=status,
        metrics=metrics,
        dataset_info=dataset_info,
        viz_exists=viz_exists,
    )


@app.route("/about")
def about():
    return render_template("about.html")


# ── Visualization route ────────────────────────────────────────────────────────

@app.route("/visualization")
def visualization():
    """Serve the latest actual-vs-predicted chart."""
    if not os.path.isfile(ml_core.VIZ_PATH):
        return jsonify(error="No visualization yet. Train the model first."), 404
    return send_from_directory(
        os.path.join(BASE_DIR, "static", "visualizations"),
        "actual_vs_predicted.png",
    )


# ══════════════════════════════════════════════════════════════════════════════
#  API endpoints
# ══════════════════════════════════════════════════════════════════════════════

@app.route("/api/upload-dataset", methods=["POST"])
def api_upload_dataset():
    """
    POST /api/upload-dataset
    Accepts a multipart/form-data file upload (field name: 'file').
    Validates the CSV, stores it, returns dataset metadata.
    """
    global _active_csv_path

    if "file" not in request.files:
        return jsonify(success=False, error="No file field in request."), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify(success=False, error="No file selected."), 400

    # ── Extension check ────────────────────────────────────────────────────────
    filename = secure_filename(file.filename)
    if not filename.lower().endswith(".csv"):
        return jsonify(success=False, error="Only CSV files are accepted."), 400

    # ── Save with unique name to prevent path traversal ────────────────────────
    unique_name = f"{uuid.uuid4().hex}_{filename}"
    save_path   = os.path.join(ml_core.DATA_DIR, unique_name)
    file.save(save_path)
    logger.info("Uploaded file saved: %s", save_path)

    # ── Validate structure and contents ───────────────────────────────────────
    try:
        info = ml_core.get_dataset_info(save_path)
    except ValueError as exc:
        os.remove(save_path)
        logger.warning("Upload rejected: %s", exc)
        return jsonify(success=False, error=str(exc)), 422

    _active_csv_path = save_path
    _save_active_csv(save_path)                        # persist across restarts
    logger.info("Active dataset updated to: %s", save_path)

    # ── Return first 10 rows as list-of-dicts for preview ─────────────────────
    import pandas as pd
    df      = pd.read_csv(save_path)
    preview = df.head(10).fillna("").to_dict(orient="records")

    return jsonify(
        success=True,
        filename=filename,
        dataset_info=info,
        preview=preview,
    ), 200


@app.route("/api/train", methods=["POST"])
def api_train():
    """
    POST /api/train
    Trains a RandomForestRegressor on the active CSV.
    Saves the pipeline, metrics, status, and visualization.
    Returns real metrics — nothing is hardcoded.
    """
    global _pipeline

    if not _active_csv_path or not os.path.isfile(_active_csv_path):
        return jsonify(
            success=False,
            error="No dataset available. Upload a CSV first.",
        ), 400

    try:
        metrics = ml_core.train_model(_active_csv_path)
    except ValueError as exc:
        logger.warning("Training failed (validation): %s", exc)
        return jsonify(success=False, error=str(exc)), 422
    except Exception as exc:
        logger.error("Training failed (unexpected): %s", exc, exc_info=True)
        return jsonify(success=False, error="Training failed unexpectedly."), 500

    # Reload the freshly trained pipeline into memory
    _load_pipeline_from_disk()
    logger.info(
        "Training complete. R²=%.4f  MAE=%.0f  RMSE=%.0f",
        metrics["r2_score"], metrics["mae"], metrics["rmse"],
    )

    return jsonify(
        success=True,
        metrics=metrics,
        viz_url="/visualization",        # JS uses this with a cache-bust timestamp
    ), 200


@app.route("/api/predict", methods=["POST"])
def api_predict():
    """
    POST /api/predict
    Body (JSON): { area_sqft, bedrooms, bathrooms, location }
    Returns:     { success, predicted_price, currency, price_per_sqft,
                   formatted_price, inputs }
    Prediction comes exclusively from the saved trained pipeline.
    """
    if _pipeline is None:
        return jsonify(
            success=False,
            error="No trained model found. Please upload a dataset and train the model first.",
        ), 503

    if not request.is_json:
        return jsonify(success=False, error="Request body must be JSON."), 415

    data = request.get_json(silent=True)
    if not data:
        return jsonify(success=False, error="Empty or malformed JSON."), 400

    # ── Extract ────────────────────────────────────────────────────────────────
    raw_area      = data.get("area_sqft")
    raw_bedrooms  = data.get("bedrooms")
    raw_bathrooms = data.get("bathrooms")
    raw_location  = data.get("location")

    if any(v is None for v in [raw_area, raw_bedrooms, raw_bathrooms, raw_location]):
        return jsonify(
            success=False,
            error="All fields are required: area_sqft, bedrooms, bathrooms, location.",
        ), 400

    # ── Coerce ─────────────────────────────────────────────────────────────────
    try:
        area      = float(raw_area)
        bedrooms  = float(raw_bedrooms)
        bathrooms = float(raw_bathrooms)
    except (TypeError, ValueError):
        return jsonify(
            success=False,
            error="area_sqft, bedrooms and bathrooms must be numeric.",
        ), 400

    location = str(raw_location).strip()

    # ── Business-rule validation ───────────────────────────────────────────────
    errors = []
    if area <= 0 or area > 50_000:
        errors.append("area_sqft must be between 1 and 50,000.")
    if bedrooms < 1 or bedrooms > 20:
        errors.append("bedrooms must be between 1 and 20.")
    if bathrooms < 1 or bathrooms > 20:
        errors.append("bathrooms must be between 1 and 20.")
    if not location:
        errors.append("location is required.")
    else:
        # Validate against locations in the trained model's metrics
        metrics   = ml_core.load_metrics()
        allowed   = metrics.get("locations", [])
        if allowed and location not in allowed:
            errors.append(
                f"Unknown location '{location}'. "
                f"Valid options: {', '.join(sorted(allowed))}."
            )
    if errors:
        return jsonify(success=False, error=" ".join(errors)), 422

    # ── Inference ──────────────────────────────────────────────────────────────
    try:
        predicted = ml_core.predict_price(
            _pipeline, area, bedrooms, bathrooms, location
        )
    except Exception as exc:
        logger.error("Prediction error: %s", exc, exc_info=True)
        return jsonify(success=False, error="Prediction failed internally."), 500

    predicted    = max(predicted, 0.0)
    price_per_sqft = predicted / area if area > 0 else 0

    logger.info(
        "Predict | area=%.0f bed=%.0f bath=%.0f loc=%s => PKR %.0f",
        area, bedrooms, bathrooms, location, predicted,
    )

    return jsonify(
        success=True,
        predicted_price=round(predicted),
        currency="PKR",
        price_per_sqft=round(price_per_sqft),
        formatted_price=f"PKR {predicted:,.0f}",
        inputs={
            "area_sqft": area,
            "bedrooms":  int(bedrooms),
            "bathrooms": int(bathrooms),
            "location":  location,
        },
    ), 200


@app.route("/api/model-status", methods=["GET"])
def api_model_status():
    """GET /api/model-status — Returns current model status from status.json."""
    status = ml_core.load_status()
    return jsonify(success=True, status=status), 200


@app.route("/api/preview", methods=["GET"])
def api_preview():
    """
    GET /api/preview
    Returns the first 10 rows of the active CSV so the dashboard
    can populate the Dataset Preview table on page load.
    """
    global _active_csv_path

    if not _active_csv_path or not os.path.isfile(_active_csv_path):
        _active_csv_path = _load_active_csv()

    if not _active_csv_path or not os.path.isfile(_active_csv_path):
        return jsonify(success=False, error="No dataset uploaded yet."), 404

    try:
        import pandas as pd
        df      = pd.read_csv(_active_csv_path)
        info    = ml_core.get_dataset_info(_active_csv_path)
        preview = df.head(10).fillna("").to_dict(orient="records")
        return jsonify(
            success=True,
            dataset_info=info,
            preview=preview,
            filename=os.path.basename(_active_csv_path),
        ), 200
    except ValueError as exc:
        return jsonify(success=False, error=str(exc)), 422
    except Exception as exc:
        logger.error("Preview error: %s", exc)
        return jsonify(success=False, error="Could not read dataset."), 500


@app.route("/api/dataset-info", methods=["GET"])
def api_dataset_info():
    """
    GET /api/dataset-info
    Returns metadata for the currently active CSV.
    Reads _active_csv_path which is persisted to disk and survives restarts.
    """
    global _active_csv_path

    # Re-resolve from disk in case this is a fresh process
    if not _active_csv_path or not os.path.isfile(_active_csv_path):
        _active_csv_path = _load_active_csv()

    if not _active_csv_path or not os.path.isfile(_active_csv_path):
        return jsonify(
            success=False,
            error="No dataset uploaded yet.",
        ), 404

    try:
        info = ml_core.get_dataset_info(_active_csv_path)
    except ValueError as exc:
        return jsonify(success=False, error=str(exc)), 422

    info["filename"] = os.path.basename(_active_csv_path)
    return jsonify(success=True, dataset_info=info), 200


@app.route("/api/metrics", methods=["GET"])
def api_metrics():
    """GET /api/metrics — Returns the most recent training metrics."""
    metrics = ml_core.load_metrics()
    if not metrics:
        return jsonify(
            success=False,
            error="No metrics yet. Train the model first.",
        ), 404

    # Normalise: ensure both r2_score and r2 are present so any JS version works
    if "r2_score" in metrics and "r2" not in metrics:
        metrics["r2"] = metrics["r2_score"]
    elif "r2" in metrics and "r2_score" not in metrics:
        metrics["r2_score"] = metrics["r2"]

    # Normalise train/test field names
    if "train_size" in metrics and "train_records" not in metrics:
        metrics["train_records"] = metrics["train_size"]
    if "test_size" in metrics and "test_records" not in metrics:
        metrics["test_records"] = metrics["test_size"]

    return jsonify(success=True, metrics=metrics), 200


# ── Error handlers ─────────────────────────────────────────────────────────────

@app.errorhandler(413)
def too_large(e):
    return jsonify(success=False, error="File too large. Maximum size is 16 MB."), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify(success=False, error="Endpoint not found."), 404

@app.errorhandler(500)
def server_error(e):
    logger.error("500: %s", e)
    return jsonify(success=False, error="Internal server error."), 500


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port  = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    logger.info("Starting HousePrice AI on http://127.0.0.1:%d", port)
    app.run(host="0.0.0.0", port=port, debug=debug)
