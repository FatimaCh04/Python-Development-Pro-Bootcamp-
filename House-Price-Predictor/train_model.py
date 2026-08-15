"""
train_model.py
Trains a RandomForestRegressor pipeline on house_data.csv.
Saves the full sklearn Pipeline to model/house_price_model.pkl
and real evaluation metrics to model/metrics.json.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')          # non-interactive backend for servers
import matplotlib.pyplot as plt
import joblib

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, 'house_data.csv')
MODEL_DIR = os.path.join(BASE_DIR, 'model')
VIZ_DIR   = os.path.join(BASE_DIR, 'visualizations')

os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(VIZ_DIR,   exist_ok=True)

# ── 1. Load & validate ────────────────────────────────────────────────────────
print("\n[1/6] Loading dataset ...")
try:
    df = pd.read_csv(DATA_PATH)
except FileNotFoundError:
    print("ERROR: house_data.csv not found. Run generate_data.py first.")
    sys.exit(1)
except pd.errors.EmptyDataError:
    print("ERROR: house_data.csv is empty.")
    sys.exit(1)

REQUIRED = {'area_sqft', 'bedrooms', 'bathrooms', 'location', 'price'}
missing  = REQUIRED - set(df.columns)
if missing:
    print(f"ERROR: Missing columns: {missing}")
    sys.exit(1)

# Drop rows with missing target or area (critical features)
df.dropna(subset=['price', 'area_sqft'], inplace=True)

print(f"    Loaded {len(df)} valid records.")
print(f"    Locations: {sorted(df['location'].unique())}")
print(f"    Missing bedrooms: {df['bedrooms'].isna().sum()} | bathrooms: {df['bathrooms'].isna().sum()}")

# ── 2. Feature / target split ─────────────────────────────────────────────────
print("\n[2/6] Splitting features and target ...")
X = df[['area_sqft', 'bedrooms', 'bathrooms', 'location']]
y = df['price']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.20, random_state=42
)
print(f"    Train: {len(X_train)} rows | Test: {len(X_test)} rows")

# ── 3. Preprocessing pipeline ─────────────────────────────────────────────────
print("\n[3/6] Building preprocessing pipeline ...")
num_features = ['area_sqft', 'bedrooms', 'bathrooms']
cat_features  = ['location']

numeric_transformer = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),   # handle NaNs
    ('scaler',  StandardScaler()),
])
categorical_transformer = Pipeline([
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('onehot',  OneHotEncoder(handle_unknown='ignore', sparse_output=False)),
])
preprocessor = ColumnTransformer([
    ('num', numeric_transformer,    num_features),
    ('cat', categorical_transformer, cat_features),
])

# ── 4. Full pipeline: preprocessor + model ────────────────────────────────────
full_pipeline = Pipeline([
    ('preprocessor', preprocessor),
    ('regressor',    RandomForestRegressor(
        n_estimators=200,
        max_depth=None,
        min_samples_split=2,
        random_state=42,
        n_jobs=-1,
    )),
])

print("\n[4/6] Training Random Forest Regressor ...")
full_pipeline.fit(X_train, y_train)

# ── 5. Evaluate ───────────────────────────────────────────────────────────────
print("\n[5/6] Evaluating on test set ...")
y_pred = full_pipeline.predict(X_test)

r2   = r2_score(y_test, y_pred)
mae  = mean_absolute_error(y_test, y_pred)
rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))

print("\n" + "=" * 48)
print("         MODEL EVALUATION RESULTS")
print("=" * 48)
print(f"  R² Score : {r2:.4f}")
print(f"  MAE      : PKR {mae:>18,.2f}")
print(f"  RMSE     : PKR {rmse:>18,.2f}")
print("=" * 48 + "\n")

# ── 6. Save model + metrics + visualization ───────────────────────────────────
print("\n[6/6] Saving artefacts ...")

# Model
model_path = os.path.join(MODEL_DIR, 'house_price_model.pkl')
joblib.dump(full_pipeline, model_path)
print(f"  [OK] Model  -> {model_path}")

# Metrics
metrics = {
    "model":            "Random Forest Regressor",
    "dataset_records":  int(len(df)),
    "train_size":       int(len(X_train)),
    "test_size":        int(len(X_test)),
    "r2_score":         round(r2, 4),
    "mae":              round(mae, 2),
    "rmse":             round(rmse, 2),
    "locations":        sorted(df['location'].unique().tolist()),
}
metrics_path = os.path.join(MODEL_DIR, 'metrics.json')
with open(metrics_path, 'w') as f:
    json.dump(metrics, f, indent=2)
print(f"  [OK] Metrics -> {metrics_path}")

# Actual vs Predicted plot
y_test_m = y_test / 1_000_000
y_pred_m = y_pred / 1_000_000

fig, ax = plt.subplots(figsize=(9, 7))
ax.scatter(y_test_m, y_pred_m, alpha=0.45, color='#1e3a8a', edgecolor='white',
           linewidth=0.4, s=60, label='Predictions')
lim = [min(y_test_m.min(), y_pred_m.min()) * 0.95,
       max(y_test_m.max(), y_pred_m.max()) * 1.05]
ax.plot(lim, lim, 'r--', lw=1.5, label='Perfect fit')
ax.set_xlim(lim); ax.set_ylim(lim)
ax.set_xlabel('Actual Price (Millions PKR)',    fontsize=12)
ax.set_ylabel('Predicted Price (Millions PKR)', fontsize=12)
ax.set_title('Actual vs Predicted House Prices — Test Set', fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, linestyle='--', alpha=0.5)

# Annotate metrics on the plot
txt = f"R²={r2:.4f}   MAE=PKR {mae/1e6:.2f}M   RMSE=PKR {rmse/1e6:.2f}M"
ax.annotate(txt, xy=(0.03, 0.95), xycoords='axes fraction',
            fontsize=9, color='#374151',
            bbox=dict(boxstyle='round,pad=0.4', fc='white', alpha=0.8))

plt.tight_layout()
viz_path = os.path.join(VIZ_DIR, 'actual_vs_predicted.png')
plt.savefig(viz_path, dpi=150)
plt.close()
print(f"  [OK] Plot   -> {viz_path}")
print("\nDone. Run app.py to start the Flask server.\n")
