import sys, os, json, traceback, shutil
BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

pycache = os.path.join(BASE, "__pycache__")
if os.path.isdir(pycache):
    shutil.rmtree(pycache, ignore_errors=True)

try:
    import subprocess
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    result = subprocess.run(
        [sys.executable, os.path.join(BASE, "run_tests.py")],
        capture_output=True, text=True, timeout=120,
        cwd=BASE, env=env, encoding="utf-8", errors="replace",
    )
    out = {
        "returncode": result.returncode,
        "stdout":     result.stdout,
        "stderr":     result.stderr[-2000:] if result.stderr else "",
    }
except Exception as e:
    out = {"error": str(e), "trace": traceback.format_exc()}

with open(os.path.join(BASE, "test_wrapper_out.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=2, ensure_ascii=False)
