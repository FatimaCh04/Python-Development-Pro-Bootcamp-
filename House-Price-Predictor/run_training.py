"""run_training.py — trains model, writes training_result.json"""
import json, os, sys, traceback

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)
RESULT_FILE = os.path.join(BASE, "training_result.json")

result = {}
try:
    import ml_core
    csv_path = os.path.join(BASE, "house_data.csv")
    if not os.path.isfile(csv_path):
        result = {"success": False, "error": "house_data.csv not found"}
    else:
        metrics = ml_core.train_model(csv_path)
        result = {
            "success":     True,
            "metrics":     metrics,
            "model_saved": os.path.isfile(ml_core.MODEL_PATH),
            "model_path":  ml_core.MODEL_PATH,
            "viz_saved":   os.path.isfile(ml_core.VIZ_PATH),
            "viz_path":    ml_core.VIZ_PATH,
        }
except Exception as e:
    result = {"success": False, "error": str(e), "trace": traceback.format_exc()}

with open(RESULT_FILE, "w") as f:
    json.dump(result, f, indent=2)
