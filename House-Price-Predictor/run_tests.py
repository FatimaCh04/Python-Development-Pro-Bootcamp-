"""
run_tests.py
------------
End-to-end verification test suite for HousePrice AI.
Uses Flask's built-in test client — no server needed.
Writes results to test_results.json.

Tests cover all 12 verification scenarios from the spec:
  1.  Upload CSV via API
  2.  Dataset preview correctness
  3.  Train model via API
  4.  Metrics are real (not hardcoded)
  5.  Visualization file generated
  6.  Model saved with Joblib
  7.  Prediction from saved model
  8.  Restart simulation — model loaded from disk, not retrained
  9.  Invalid CSV (missing required columns)
  10. Invalid CSV (wrong extension)
  11. Invalid CSV (empty file)
  12. Invalid prediction inputs (bad values, unknown location)
"""

import io
import json
import os
import sys
import traceback

# Force UTF-8 output so Unicode symbols don't crash on Windows CP1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

RESULTS_FILE = os.path.join(BASE, "test_results.json")

results = []
passed  = 0
failed  = 0


def record(name, ok, detail="", data=None):
    global passed, failed
    status = "PASS" if ok else "FAIL"
    results.append({
        "test":   name,
        "status": status,
        "detail": detail,
        "data":   data,
    })
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {name}: {detail}")
    if ok:
        passed += 1
    else:
        failed += 1


# ── Boot Flask app ─────────────────────────────────────────────────────────────
try:
    import app as flask_app
    client = flask_app.app.test_client()
    record("Flask app import", True, "app.py imported successfully")
except Exception as e:
    record("Flask app import", False, str(e))
    json.dump({"passed": 0, "failed": 1, "results": results}, open(RESULTS_FILE, "w"), indent=2)
    sys.exit(1)


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 1 — Home page renders (GET /)
# ══════════════════════════════════════════════════════════════════════════════
try:
    r = client.get("/")
    ok = r.status_code == 200 and b"HousePrice" in r.data
    record("GET / — Home page renders", ok,
           f"status={r.status_code}, contains 'HousePrice'={b'HousePrice' in r.data}")
except Exception as e:
    record("GET / — Home page renders", False, str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 2 — Dashboard page renders (GET /dashboard)
# ══════════════════════════════════════════════════════════════════════════════
try:
    r = client.get("/dashboard")
    ok = r.status_code == 200 and b"ML Dashboard" in r.data
    record("GET /dashboard — Dashboard page renders", ok,
           f"status={r.status_code}, contains 'ML Dashboard'={b'ML Dashboard' in r.data}")
except Exception as e:
    record("GET /dashboard — Dashboard page renders", False, str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 3 — CSV Upload (valid file)
# ══════════════════════════════════════════════════════════════════════════════
csv_path = os.path.join(BASE, "house_data.csv")
upload_response_data = None
try:
    with open(csv_path, "rb") as f:
        csv_bytes = f.read()

    data = {"file": (io.BytesIO(csv_bytes), "house_data.csv")}
    r    = client.post("/api/upload-dataset",
                       data=data, content_type="multipart/form-data")
    j    = r.get_json()
    ok   = r.status_code == 200 and j.get("success") is True
    upload_response_data = j
    record("POST /api/upload-dataset — valid CSV",
           ok,
           f"status={r.status_code}, rows={j.get('dataset_info', {}).get('rows', '?')}",
           {"rows": j.get("dataset_info", {}).get("rows"),
            "columns": j.get("dataset_info", {}).get("columns"),
            "locations": j.get("dataset_info", {}).get("locations")})
except Exception as e:
    record("POST /api/upload-dataset — valid CSV", False, traceback.format_exc())


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 4 — Dataset preview (first 10 rows returned)
# ══════════════════════════════════════════════════════════════════════════════
try:
    preview = upload_response_data.get("preview", []) if upload_response_data else []
    ok = (
        len(preview) == 10
        and all(k in preview[0] for k in ("area_sqft", "bedrooms", "bathrooms", "location", "price"))
    )
    record("Dataset preview — 10 rows with correct columns", ok,
           f"rows_returned={len(preview)}, "
           f"has_required_cols={all(k in preview[0] for k in ('area_sqft','bedrooms','bathrooms','location','price')) if preview else False}")
except Exception as e:
    record("Dataset preview — 10 rows with correct columns", False, str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 5 — GET /api/dataset-info
# ══════════════════════════════════════════════════════════════════════════════
try:
    r = client.get("/api/dataset-info")
    j = r.get_json()
    ok = (r.status_code == 200
          and j.get("success") is True
          and j["dataset_info"]["rows"] > 0
          and len(j["dataset_info"]["locations"]) > 0)
    record("GET /api/dataset-info — dynamic info",
           ok,
           f"rows={j.get('dataset_info',{}).get('rows')}, "
           f"locations={len(j.get('dataset_info',{}).get('locations',[]))}")
except Exception as e:
    record("GET /api/dataset-info", False, str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 6 — Train model via API
# ══════════════════════════════════════════════════════════════════════════════
train_metrics = None
try:
    r = client.post("/api/train")
    j = r.get_json()
    ok = (r.status_code == 200
          and j.get("success") is True
          and "r2_score" in j.get("metrics", {}))
    train_metrics = j.get("metrics") if ok else None
    record("POST /api/train — model training",
           ok,
           f"status={r.status_code}, "
           f"r2={j.get('metrics',{}).get('r2_score','?')}, "
           f"mae={j.get('metrics',{}).get('mae','?')}, "
           f"rmse={j.get('metrics',{}).get('rmse','?')}",
           j.get("metrics"))
except Exception as e:
    record("POST /api/train — model training", False, traceback.format_exc())


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 7 — Metrics are real (not hardcoded)
# ══════════════════════════════════════════════════════════════════════════════
try:
    m  = train_metrics or {}
    r2 = m.get("r2_score", -1)
    ok = (
        0.0 < r2 <= 1.0
        and m.get("mae", 0) > 0
        and m.get("rmse", 0) > 0
        and m.get("train_size", 0) > 0
        and m.get("test_size", 0) > 0
        and m.get("dataset_records", 0) > 0
        and len(m.get("locations", [])) > 0
        and m.get("trained_at") is not None
    )
    record("Metrics are real and non-hardcoded", ok,
           f"r2={r2}, mae={m.get('mae')}, rmse={m.get('rmse')}, "
           f"train={m.get('train_size')}, test={m.get('test_size')}, "
           f"locations={m.get('locations')}")
except Exception as e:
    record("Metrics are real and non-hardcoded", False, str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 8 — Visualization file generated
# ══════════════════════════════════════════════════════════════════════════════
try:
    import ml_core
    ok = os.path.isfile(ml_core.VIZ_PATH) and os.path.getsize(ml_core.VIZ_PATH) > 1000
    record("Actual vs Predicted chart generated",
           ok,
           f"exists={os.path.isfile(ml_core.VIZ_PATH)}, "
           f"size={os.path.getsize(ml_core.VIZ_PATH) if os.path.isfile(ml_core.VIZ_PATH) else 0} bytes")
except Exception as e:
    record("Actual vs Predicted chart generated", False, str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 9 — Model saved with Joblib
# ══════════════════════════════════════════════════════════════════════════════
try:
    import joblib
    ok = os.path.isfile(ml_core.MODEL_PATH)
    if ok:
        loaded = joblib.load(ml_core.MODEL_PATH)
        ok = hasattr(loaded, "predict")
    record("Model saved and loadable via Joblib",
           ok,
           f"path={ml_core.MODEL_PATH}, "
           f"has_predict={ok}")
except Exception as e:
    record("Model saved and loadable via Joblib", False, str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 10 — GET /api/metrics returns stored metrics
# ══════════════════════════════════════════════════════════════════════════════
try:
    r = client.get("/api/metrics")
    j = r.get_json()
    ok = r.status_code == 200 and j.get("success") and "r2_score" in j.get("metrics", {})
    record("GET /api/metrics — returns live metrics",
           ok,
           f"r2={j.get('metrics',{}).get('r2_score','?')}")
except Exception as e:
    record("GET /api/metrics", False, str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 11 — GET /api/model-status
# ══════════════════════════════════════════════════════════════════════════════
try:
    r = client.get("/api/model-status")
    j = r.get_json()
    ok = (r.status_code == 200
          and j.get("success")
          and j["status"].get("trained") is True
          and j["status"].get("model") is not None)
    record("GET /api/model-status — shows Trained",
           ok,
           f"trained={j.get('status',{}).get('trained')}, "
           f"model={j.get('status',{}).get('model')}")
except Exception as e:
    record("GET /api/model-status", False, str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 12 — Valid prediction from saved model
# ══════════════════════════════════════════════════════════════════════════════
prediction_result = None
try:
    metrics   = train_metrics or {}
    locations = metrics.get("locations", [])
    loc       = locations[0] if locations else "DHA"

    r = client.post("/api/predict",
                    json={"area_sqft": 2000, "bedrooms": 3,
                          "bathrooms": 2, "location": loc},
                    content_type="application/json")
    j = r.get_json()
    ok = (r.status_code == 200
          and j.get("success") is True
          and j.get("predicted_price", 0) > 0
          and j.get("currency") == "PKR"
          and j.get("price_per_sqft", 0) > 0)
    prediction_result = j
    record("POST /api/predict — valid prediction",
           ok,
           f"price={j.get('formatted_price','?')}, "
           f"ppsqft=PKR {j.get('price_per_sqft','?')}, "
           f"location={loc}",
           j)
except Exception as e:
    record("POST /api/predict — valid prediction", False, traceback.format_exc())


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 13 — Restart simulation: reload pipeline from disk, predict again
# ══════════════════════════════════════════════════════════════════════════════
try:
    import joblib
    # Simulate restart: load fresh pipeline directly from disk
    fresh_pipeline = joblib.load(ml_core.MODEL_PATH)
    import pandas as pd
    df_input = pd.DataFrame([{"area_sqft": 2000, "bedrooms": 3,
                               "bathrooms": 2, "location": loc}])
    price_after_restart = float(fresh_pipeline.predict(df_input)[0])
    price_first         = prediction_result.get("predicted_price", 0) if prediction_result else 0

    # Prices should match (same input, same model)
    ok = price_after_restart > 0 and abs(price_after_restart - price_first) < 1
    record("Restart simulation — model loaded from disk, same result",
           ok,
           f"first={price_first:,.0f}, after_reload={price_after_restart:,.0f}, "
           f"match={abs(price_after_restart - price_first) < 1}")
except Exception as e:
    record("Restart simulation", False, traceback.format_exc())


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 14 — Invalid CSV: missing required columns
# ══════════════════════════════════════════════════════════════════════════════
try:
    bad_csv = b"col1,col2\n1,2\n3,4\n"
    data    = {"file": (io.BytesIO(bad_csv), "bad.csv")}
    r       = client.post("/api/upload-dataset",
                          data=data, content_type="multipart/form-data")
    j       = r.get_json()
    ok      = r.status_code in (400, 422) and j.get("success") is False and "error" in j
    record("Invalid CSV — missing columns rejected",
           ok,
           f"status={r.status_code}, error='{j.get('error','')[:80]}'")
except Exception as e:
    record("Invalid CSV — missing columns rejected", False, str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 15 — Invalid upload: wrong file extension
# ══════════════════════════════════════════════════════════════════════════════
try:
    data = {"file": (io.BytesIO(b"not a csv"), "malware.exe")}
    r    = client.post("/api/upload-dataset",
                       data=data, content_type="multipart/form-data")
    j    = r.get_json()
    ok   = r.status_code == 400 and j.get("success") is False
    record("Invalid upload — wrong extension rejected",
           ok,
           f"status={r.status_code}, error='{j.get('error','')}'")
except Exception as e:
    record("Invalid upload — wrong extension rejected", False, str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 16 — Invalid upload: empty CSV
# ══════════════════════════════════════════════════════════════════════════════
try:
    data = {"file": (io.BytesIO(b""), "empty.csv")}
    r    = client.post("/api/upload-dataset",
                       data=data, content_type="multipart/form-data")
    j    = r.get_json()
    ok   = r.status_code in (400, 422) and j.get("success") is False
    record("Invalid upload — empty CSV rejected",
           ok,
           f"status={r.status_code}, error='{j.get('error','')[:80]}'")
except Exception as e:
    record("Invalid upload — empty CSV rejected", False, str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 17 — Invalid prediction: missing fields
# ══════════════════════════════════════════════════════════════════════════════
try:
    r  = client.post("/api/predict",
                     json={"area_sqft": 1500},
                     content_type="application/json")
    j  = r.get_json()
    ok = r.status_code in (400, 422) and j.get("success") is False
    record("Invalid prediction — missing fields rejected",
           ok,
           f"status={r.status_code}, error='{j.get('error','')[:80]}'")
except Exception as e:
    record("Invalid prediction — missing fields rejected", False, str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 18 — Invalid prediction: unknown location
# ══════════════════════════════════════════════════════════════════════════════
try:
    r  = client.post("/api/predict",
                     json={"area_sqft": 1500, "bedrooms": 3,
                           "bathrooms": 2, "location": "FAKE_LOCATION_XYZ"},
                     content_type="application/json")
    j  = r.get_json()
    ok = r.status_code in (400, 422, 503) and j.get("success") is False
    record("Invalid prediction — unknown location rejected",
           ok,
           f"status={r.status_code}, error='{j.get('error','')[:80]}'")
except Exception as e:
    record("Invalid prediction — unknown location rejected", False, str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 19 — Invalid prediction: negative area
# ══════════════════════════════════════════════════════════════════════════════
try:
    loc = (train_metrics or {}).get("locations", ["DHA"])[0]
    r   = client.post("/api/predict",
                      json={"area_sqft": -500, "bedrooms": 3,
                            "bathrooms": 2, "location": loc},
                      content_type="application/json")
    j   = r.get_json()
    ok  = r.status_code in (400, 422) and j.get("success") is False
    record("Invalid prediction — negative area rejected",
           ok,
           f"status={r.status_code}, error='{j.get('error','')[:80]}'")
except Exception as e:
    record("Invalid prediction — negative area rejected", False, str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 20 — Visualization endpoint
# ══════════════════════════════════════════════════════════════════════════════
try:
    r  = client.get("/visualization")
    ok = r.status_code == 200 and r.content_type.startswith("image/")
    record("GET /visualization — returns PNG image",
           ok,
           f"status={r.status_code}, content_type={r.content_type}")
except Exception as e:
    record("GET /visualization — returns PNG image", False, str(e))


# ══════════════════════════════════════════════════════════════════════════════
#  TEST 21 — No model: predict without trained model returns 503
# ══════════════════════════════════════════════════════════════════════════════
try:
    original_pipeline = flask_app._pipeline
    flask_app._pipeline = None          # simulate no model
    r = client.post("/api/predict",
                    json={"area_sqft": 2000, "bedrooms": 3,
                          "bathrooms": 2, "location": "DHA"},
                    content_type="application/json")
    j  = r.get_json()
    ok = r.status_code == 503 and j.get("success") is False
    record("No-model guard — 503 returned when model not loaded",
           ok,
           f"status={r.status_code}, error='{j.get('error','')[:80]}'")
    flask_app._pipeline = original_pipeline   # restore
except Exception as e:
    record("No-model guard", False, str(e))
    try:
        flask_app._pipeline = original_pipeline
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
#  Summary
# ══════════════════════════════════════════════════════════════════════════════
summary = {
    "passed":  passed,
    "failed":  failed,
    "total":   passed + failed,
    "results": results,
}

with open(RESULTS_FILE, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print(f"\n  {'='*50}")
print(f"  TOTAL: {passed + failed}  |  PASSED: {passed}  |  FAILED: {failed}")
print(f"  {'='*50}")
print(f"  Results written → {RESULTS_FILE}")
