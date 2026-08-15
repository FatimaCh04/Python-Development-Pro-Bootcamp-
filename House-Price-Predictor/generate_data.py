"""
generate_data.py
Generates a realistic synthetic Pakistani real estate dataset.
"""
import pandas as pd
import numpy as np

np.random.seed(42)
N = 1200  # slightly over 1000 for robustness

# --- Location configuration (name, base_price_per_sqft, tier) ---
LOCATIONS = {
    'DHA':              {'land_rate': 28000, 'construction': (6000, 9000)},
    'Clifton':          {'land_rate': 26000, 'construction': (5500, 8500)},
    'Bahria Town':      {'land_rate': 22000, 'construction': (5000, 8000)},
    'Gulberg':          {'land_rate': 20000, 'construction': (4500, 7500)},
    'Model Town':       {'land_rate': 18000, 'construction': (4000, 7000)},
    'PECHS':            {'land_rate': 16000, 'construction': (4000, 6500)},
    'Gulshan':          {'land_rate': 12000, 'construction': (3500, 6000)},
    'North Nazimabad':  {'land_rate': 10000, 'construction': (3000, 5500)},
}

location_names = list(LOCATIONS.keys())

records = []
for _ in range(N):
    loc = np.random.choice(location_names)
    cfg = LOCATIONS[loc]

    # Area: skewed toward mid-range (500–6000 sqft)
    area = int(np.random.triangular(500, 1800, 6000))

    # Bedrooms: loosely correlated with area
    bed_mean = np.clip(area / 800, 1, 7)
    bedrooms = int(np.clip(np.round(np.random.normal(bed_mean, 0.8)), 1, 8))

    # Bathrooms: close to bedrooms (slightly less or equal)
    bathrooms = int(np.clip(np.random.randint(max(1, bedrooms - 1), bedrooms + 2), 1, 9))

    # Land value
    land_value = area * cfg['land_rate']

    # Construction cost per sqft (varies by location quality)
    con_low, con_high = cfg['construction']
    construction_cost = area * np.random.randint(con_low, con_high)

    # Room premium
    room_premium = (bedrooms * 600_000) + (bathrooms * 350_000)

    # Introduce realistic noise ±12%
    noise = np.random.uniform(0.88, 1.12)
    price = (land_value + construction_cost + room_premium) * noise

    # Introduce ~2% missing values for bedrooms/bathrooms (handled by pipeline)
    if np.random.random() < 0.02:
        bedrooms = np.nan
    if np.random.random() < 0.02:
        bathrooms = np.nan

    records.append({
        'area_sqft': area,
        'bedrooms':  bedrooms,
        'bathrooms': bathrooms,
        'location':  loc,
        'price':     round(price, 2),
    })

df = pd.DataFrame(records)
df.to_csv('house_data.csv', index=False)
print(f"house_data.csv created — {len(df)} records, columns: {list(df.columns)}")
