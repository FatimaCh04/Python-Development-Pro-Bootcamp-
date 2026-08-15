"""
acceptance_test.py
------------------
Full end-to-end acceptance test for the dynamic dashboard data flow.
Tests the exact sequence required:
  Dataset A → upload → info → train → metrics → graph
  Dataset B → upload → info → train → metrics MUST change → graph MUST regenerate
  Home predictor must use the latest trained model after each training run.

Writes results to acceptance_results.json.
"""
import io, json, os, sys, shutil, time, traceback

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

# Clear pycache so updated files are used
pycache = os.path.join(BASE, "__pycache__")
if os.path.isdir(pycache):
    shutil.rmtree(pycache, ignore_errors=True)

OUT_FILE = os.path.join(BASE, "acceptance_results.json")

results  = []
passed   = 0
failed   = 0

def chk(name, ok, detail="", data=None):
    global passed, failed
    results.append({"test": name, "status": "PASS" if ok else "FAIL",
                    "detail": detail, "data": data})
    tag = "PASS" if ok else "FAIL"
    print(f"  [{tag}] {name}")
    if detail: print(f"         {detail}")
    if ok: passed += 1
    else:  failed += 1

def fmt(n):
    try:    return f"{int(round(float(n))):,}"
    except: return str(n)

# ── Boot app ──────────────────────────────────────────────────────────────────
try:
    import app as flask_app
    client = flask_app.app.test_client()
    chk("Flask app boots", True, "app.py imported OK")
except Exception:
    chk("Flask app boots", False, traceback.format_exc())
    json.dump({"passed": 0, "failed": 1, "results": results},
              open(OUT_FILE, "w"), indent=2)
    sys.exit(1)

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — Dataset A  (100 rows, 5 locations: Gulshan/PECHS/NorthNazimabad/Clifton/Gulberg)
#             Lower price range  ~8M–67M PKR
# ─────────────────────────────────────────────────────────────────────────────
print("\n── DATASET A ──────────────────────────────────────────────────────────")

A_PATH = os.path.join(BASE, "test_dataset_a.csv")

# 1. Upload A
with open(A_PATH, "rb") as f:
    r = client.post("/api/upload-dataset",
                    data={"file": (io.BytesIO(f.read()), "test_dataset_a.csv")},
                    content_type="multipart/form-data")
j = r.get_json()
chk("A: Upload succeeds",
    r.status_code == 200 and j.get("success"),
    f"status={r.status_code}, rows={j.get('dataset_info',{}).get('rows','?')}")

a_rows      = j.get("dataset_info", {}).get("rows", 0)
a_locations = j.get("dataset_info", {}).get("locations", [])

# 2. Dataset info API after upload
r2 = client.get("/api/dataset-info")
j2 = r2.get_json()
chk("A: /api/dataset-info returns A rows",
    r2.status_code == 200 and j2.get("success") and j2["dataset_info"]["rows"] == a_rows,
    f"rows={j2.get('dataset_info',{}).get('rows','?')} expected={a_rows}")
chk("A: /api/dataset-info has correct locations",
    set(j2.get("dataset_info",{}).get("locations",[])) == set(a_locations),
    f"locations={j2.get('dataset_info',{}).get('locations','?')}")

# 3. Train on A
r3 = client.post("/api/train")
j3 = r3.get_json()
chk("A: Training succeeds",
    r3.status_code == 200 and j3.get("success"),
    f"status={r3.status_code}")

a_metrics = j3.get("metrics", {})
a_r2   = a_metrics.get("r2_score")
a_mae  = a_metrics.get("mae")
a_rmse = a_metrics.get("rmse")
a_train = a_metrics.get("train_size")
a_test  = a_metrics.get("test_size")
a_total = a_metrics.get("dataset_records")

chk("A: Metrics are present and non-zero",
    all(v is not None and v > 0 for v in [a_r2, a_mae, a_rmse, a_train, a_test]),
    f"R2={a_r2}, MAE=PKR {fmt(a_mae)}, RMSE=PKR {fmt(a_rmse)}, "
    f"train={a_train}, test={a_test}")
chk("A: Train+Test = total records",
    (a_train or 0) + (a_test or 0) == (a_total or -1),
    f"{a_train}+{a_test}={a_train+a_test if a_train and a_test else '?'} == {a_total}")
chk("A: viz_url returned",
    j3.get("viz_url") is not None,
    f"viz_url={j3.get('viz_url')}")

# 4. /api/metrics after training A
r4 = client.get("/api/metrics")
j4 = r4.get_json()
chk("A: /api/metrics returns A metrics",
    r4.status_code == 200 and j4.get("success")
    and j4["metrics"].get("r2_score") == a_r2,
    f"R2={j4.get('metrics',{}).get('r2_score','?')}")

# 5. Chart file exists and is non-empty
import ml_core as _mc
viz_size_a = os.path.getsize(_mc.VIZ_PATH) if os.path.isfile(_mc.VIZ_PATH) else 0
chk("A: Chart PNG exists and non-empty",
    viz_size_a > 1000,
    f"size={viz_size_a} bytes")

# Record mtime for comparison
viz_mtime_a = os.path.getmtime(_mc.VIZ_PATH) if os.path.isfile(_mc.VIZ_PATH) else 0

# 6. /visualization endpoint returns a PNG
r5 = client.get("/visualization")
chk("A: /visualization returns PNG",
    r5.status_code == 200 and r5.content_type.startswith("image/"),
    f"status={r5.status_code}, content_type={r5.content_type}")

# 7. Predict with A's model (use a known A location)
a_loc = a_locations[0] if a_locations else "Gulshan"
r6 = client.post("/api/predict",
                 json={"area_sqft": 1500, "bedrooms": 3,
                       "bathrooms": 2, "location": a_loc},
                 content_type="application/json")
j6 = r6.get_json()
chk("A: Prediction works after training A",
    r6.status_code == 200 and j6.get("success") and j6.get("predicted_price", 0) > 0,
    f"price={j6.get('formatted_price','?')}, location={a_loc}")
a_pred_price = j6.get("predicted_price", 0)

# 8. /api/model-status shows correct A training info
r7 = client.get("/api/model-status")
j7 = r7.get_json()
st = j7.get("status", {})
chk("A: Model status = Trained, train_records = train_size",
    j7.get("success") and st.get("trained") is True
    and st.get("train_records") == a_train,
    f"trained={st.get('trained')}, train_records={st.get('train_records')} expected={a_train}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — Dataset B  (200 rows, 3 locations: DHA/Bahria Town/Model Town)
#             Higher price range  ~18M–382M PKR  (very different from A)
# ─────────────────────────────────────────────────────────────────────────────
print("\n── DATASET B ──────────────────────────────────────────────────────────")

# Small sleep so mtime is distinguishable
time.sleep(0.5)

B_PATH = os.path.join(BASE, "test_dataset_b.csv")

# 9. Upload B
with open(B_PATH, "rb") as f:
    r = client.post("/api/upload-dataset",
                    data={"file": (io.BytesIO(f.read()), "test_dataset_b.csv")},
                    content_type="multipart/form-data")
j = r.get_json()
chk("B: Upload succeeds",
    r.status_code == 200 and j.get("success"),
    f"status={r.status_code}, rows={j.get('dataset_info',{}).get('rows','?')}")

b_rows      = j.get("dataset_info", {}).get("rows", 0)
b_locations = j.get("dataset_info", {}).get("locations", [])

# 10. Dataset info must change — B has different rows and locations
r8 = client.get("/api/dataset-info")
j8 = r8.get_json()
info_b = j8.get("dataset_info", {})
chk("B: /api/dataset-info rows changed from A",
    info_b.get("rows") == b_rows and b_rows != a_rows,
    f"A rows={a_rows}, B rows={b_rows}")
chk("B: /api/dataset-info locations changed from A",
    set(info_b.get("locations", [])) != set(a_locations),
    f"A locs={sorted(a_locations)}, B locs={sorted(info_b.get('locations',[]))}")
chk("B: /api/dataset-info filename reflects B",
    "test_dataset_b" in info_b.get("filename",""),
    f"filename={info_b.get('filename','?')}")

# 11. Train on B
r9 = client.post("/api/train")
j9 = r9.get_json()
chk("B: Training succeeds",
    r9.status_code == 200 and j9.get("success"),
    f"status={r9.status_code}")

b_metrics = j9.get("metrics", {})
b_r2   = b_metrics.get("r2_score")
b_mae  = b_metrics.get("mae")
b_rmse = b_metrics.get("rmse")
b_train = b_metrics.get("train_size")
b_test  = b_metrics.get("test_size")
b_total = b_metrics.get("dataset_records")
b_locs  = b_metrics.get("locations", [])

chk("B: Metrics are present and non-zero",
    all(v is not None and v > 0 for v in [b_r2, b_mae, b_rmse, b_train, b_test]),
    f"R2={b_r2}, MAE=PKR {fmt(b_mae)}, RMSE=PKR {fmt(b_rmse)}, "
    f"train={b_train}, test={b_test}")

# 12. Metrics MUST differ from A (different dataset → different numbers)
chk("B: R2 differs from A",
    b_r2 != a_r2,
    f"A R2={a_r2}, B R2={b_r2}")
chk("B: MAE differs from A",
    b_mae != a_mae,
    f"A MAE=PKR {fmt(a_mae)}, B MAE=PKR {fmt(b_mae)}")
chk("B: RMSE differs from A",
    b_rmse != a_rmse,
    f"A RMSE=PKR {fmt(a_rmse)}, B RMSE=PKR {fmt(b_rmse)}")
chk("B: Train size differs from A  (B has more records)",
    b_train != a_train,
    f"A train={a_train}, B train={b_train}")
chk("B: Locations in metrics differ from A",
    set(b_locs) != set(a_locations),
    f"A={sorted(a_locations)}, B={sorted(b_locs)}")

# 13. /api/metrics returns B values
r10 = client.get("/api/metrics")
j10 = r10.get_json()
chk("B: /api/metrics returns B R2",
    j10.get("success") and j10["metrics"].get("r2_score") == b_r2,
    f"R2 from API={j10.get('metrics',{}).get('r2_score','?')} expected={b_r2}")

# 14. Chart was regenerated (mtime changed or size changed)
viz_size_b  = os.path.getsize(_mc.VIZ_PATH) if os.path.isfile(_mc.VIZ_PATH) else 0
viz_mtime_b = os.path.getmtime(_mc.VIZ_PATH) if os.path.isfile(_mc.VIZ_PATH) else 0
chk("B: Chart PNG regenerated after training B",
    viz_mtime_b > viz_mtime_a or viz_size_b != viz_size_a,
    f"A mtime={viz_mtime_a:.3f} size={viz_size_a}B  "
    f"B mtime={viz_mtime_b:.3f} size={viz_size_b}B")

# 15. Home predictor uses B's model — B locations must work, A locations rejected
b_loc = b_locations[0] if b_locations else "DHA"
r11 = client.post("/api/predict",
                  json={"area_sqft": 2000, "bedrooms": 4,
                        "bathrooms": 3, "location": b_loc},
                  content_type="application/json")
j11 = r11.get_json()
chk("B: Prediction works with B location after training B",
    r11.status_code == 200 and j11.get("success"),
    f"price={j11.get('formatted_price','?')}, location={b_loc}")
b_pred_price = j11.get("predicted_price", 0)

# Old A-only location rejected (A had Gulshan; B has DHA/Bahria Town/Model Town)
a_only_loc = next((l for l in a_locations if l not in b_locs), None)
if a_only_loc:
    r12 = client.post("/api/predict",
                      json={"area_sqft": 2000, "bedrooms": 4,
                            "bathrooms": 3, "location": a_only_loc},
                      content_type="application/json")
    j12 = r12.get_json()
    chk("B: A-only location rejected after training B",
        r12.status_code in (400, 422) and not j12.get("success"),
        f"location={a_only_loc}, status={r12.status_code}, error={j12.get('error','?')[:60]}")

# 16. Price differs between A model and B model (same input area, different model)
chk("B: B prediction price different from A prediction price",
    b_pred_price != a_pred_price,
    f"A pred=PKR {fmt(a_pred_price)}, B pred=PKR {fmt(b_pred_price)}")

# 17. Model status reflects B training
r13 = client.get("/api/model-status")
j13 = r13.get_json()
st2 = j13.get("status", {})
chk("B: Model status train_records = B train_size",
    j13.get("success") and st2.get("train_records") == b_train,
    f"train_records={st2.get('train_records')} expected={b_train}")
chk("B: Model status dataset_file contains B filename",
    "test_dataset_b" in (st2.get("dataset_file") or ""),
    f"dataset_file={st2.get('dataset_file','?')}")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — Restart simulation: reload pipeline from disk, predict again
# ─────────────────────────────────────────────────────────────────────────────
print("\n── RESTART SIMULATION ─────────────────────────────────────────────────")

import joblib as _jl
fresh = _jl.load(_mc.MODEL_PATH)
import pandas as _pd
inp = _pd.DataFrame([{"area_sqft": 2000, "bedrooms": 4,
                       "bathrooms": 3, "location": b_loc}])
price_reload = float(fresh.predict(inp)[0])
chk("Restart: reload from disk gives same price as in-memory prediction",
    abs(price_reload - b_pred_price) < 1,
    f"in-memory={fmt(b_pred_price)}, from-disk={fmt(price_reload)}")

# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — /api/dataset-info after restart (reads persisted active path)
# ─────────────────────────────────────────────────────────────────────────────
print("\n── PERSISTENCE CHECK ──────────────────────────────────────────────────")
r14 = client.get("/api/dataset-info")
j14 = r14.get_json()
chk("Persistence: /api/dataset-info still returns B info",
    r14.status_code == 200 and j14.get("success")
    and j14["dataset_info"]["rows"] == b_rows,
    f"rows={j14.get('dataset_info',{}).get('rows','?')} expected={b_rows}")

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
summary = {
    "passed": passed, "failed": failed, "total": passed + failed,
    "dataset_a": {
        "rows":       a_rows,
        "locations":  sorted(a_locations),
        "r2":         a_r2,
        "mae":        a_mae,
        "rmse":       a_rmse,
        "train_size": a_train,
        "test_size":  a_test,
    },
    "dataset_b": {
        "rows":       b_rows,
        "locations":  sorted(b_locations),
        "r2":         b_r2,
        "mae":        b_mae,
        "rmse":       b_rmse,
        "train_size": b_train,
        "test_size":  b_test,
    },
    "results": results,
}

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)

print(f"\n  {'='*54}")
print(f"  TOTAL: {passed+failed}  |  PASSED: {passed}  |  FAILED: {failed}")
print(f"  {'='*54}")
print(f"  Results → {OUT_FILE}")
