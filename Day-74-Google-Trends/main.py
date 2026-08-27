import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# ==========================================================
# 1. TESLA: Google Search Trend vs Stock Price
# ==========================================================

df_tesla = pd.read_csv("TESLA Search Trend vs Price.csv")

print("Tesla Dataset:")
print(df_tesla.head())
print("\nTesla Dataset Info:")
print(df_tesla.info())

# Convert MONTH column to datetime
df_tesla["MONTH"] = pd.to_datetime(df_tesla["MONTH"])

# Create figure and two y-axes
fig, ax1 = plt.subplots(figsize=(14, 8))

ax2 = ax1.twinx()

ax1.set_xlabel("Date")
ax1.set_ylabel("TSLA Stock Price")
ax2.set_ylabel("Google Search Trend")

ax1.plot(
    df_tesla["MONTH"],
    df_tesla["TSLA_USD_CLOSE"],
    linewidth=3
)

ax2.plot(
    df_tesla["MONTH"],
    df_tesla["TSLA_WEB_SEARCH"],
    linewidth=3
)

plt.title("Tesla Web Search vs Stock Price")

plt.tight_layout()
plt.show()


# ==========================================================
# 2. BITCOIN: Google Search Trend vs Price
# ==========================================================

df_btc_search = pd.read_csv("Bitcoin Search Trend.csv")
df_btc_price = pd.read_csv("Daily Bitcoin Price.csv")

print("\nBitcoin Search Dataset:")
print(df_btc_search.head())

print("\nBitcoin Price Dataset:")
print(df_btc_price.head())

# Convert dates
df_btc_search["MONTH"] = pd.to_datetime(df_btc_search["MONTH"])
df_btc_price["DATE"] = pd.to_datetime(df_btc_price["DATE"])

# Check missing values
print("\nBitcoin Price Missing Values:")
print(df_btc_price.isna().sum())

# Remove missing values
df_btc_price = df_btc_price.dropna()

# Resample daily Bitcoin prices to monthly
df_btc_monthly = df_btc_price.resample(
    "ME",
    on="DATE"
).last()

# Plot
fig, ax1 = plt.subplots(figsize=(14, 8))

ax2 = ax1.twinx()

ax1.set_xlabel("Date")
ax1.set_ylabel("Bitcoin Price")
ax2.set_ylabel("Google Search Trend")

ax1.plot(
    df_btc_monthly.index,
    df_btc_monthly["CLOSE"],
    linewidth=3,
    linestyle="--"
)

ax2.plot(
    df_btc_search["MONTH"],
    df_btc_search["BTC_NEWS_SEARCH"],
    linewidth=3
)

plt.title("Bitcoin Price vs Google Search Trend")

plt.tight_layout()
plt.show()


# ==========================================================
# 3. UNEMPLOYMENT BENEFITS SEARCH VS UNEMPLOYMENT RATE
# ==========================================================

df_unemployment = pd.read_csv(
    "UE Benefits Search vs UE Rate 2004-19.csv"
)

print("\nUnemployment Dataset:")
print(df_unemployment.head())

# Convert MONTH to datetime
df_unemployment["MONTH"] = pd.to_datetime(
    df_unemployment["MONTH"]
)

# Plot
fig, ax1 = plt.subplots(figsize=(14, 8))

ax2 = ax1.twinx()

ax1.set_xlabel("Date")
ax1.set_ylabel("FRED U/E Rate")
ax2.set_ylabel("Search Trend")

ax1.plot(
    df_unemployment["MONTH"],
    df_unemployment["UNRATE"],
    linewidth=3,
    linestyle="--"
)

ax2.plot(
    df_unemployment["MONTH"],
    df_unemployment["UE_BENEFITS_WEB_SEARCH"],
    linewidth=3
)

plt.title(
    'Monthly Search of "Unemployment Benefits" '
    'in the U.S. vs the U/E Rate'
)

ax1.grid(
    linestyle="--",
    alpha=0.5
)

# Format dates
ax1.xaxis.set_major_locator(
    mdates.YearLocator()
)

ax1.xaxis.set_major_formatter(
    mdates.DateFormatter("%Y")
)

fig.autofmt_xdate()

plt.tight_layout()
plt.show()


# ==========================================================
# 4. SIX-MONTH ROLLING AVERAGE
# ==========================================================

rolling_df = df_unemployment[
    [
        "UE_BENEFITS_WEB_SEARCH",
        "UNRATE"
    ]
].rolling(
    window=6
).mean()

fig, ax1 = plt.subplots(figsize=(14, 8))

ax2 = ax1.twinx()

ax1.set_xlabel("Date")
ax1.set_ylabel("FRED U/E Rate")
ax2.set_ylabel("Search Trend")

ax1.plot(
    df_unemployment["MONTH"],
    rolling_df["UNRATE"],
    linewidth=3,
    linestyle="--"
)

ax2.plot(
    df_unemployment["MONTH"],
    rolling_df["UE_BENEFITS_WEB_SEARCH"],
    linewidth=3
)

plt.title(
    '6-Month Rolling Average: '
    '"Unemployment Benefits" vs U/E Rate'
)

ax1.grid(
    linestyle="--",
    alpha=0.5
)

ax1.xaxis.set_major_locator(
    mdates.YearLocator()
)

ax1.xaxis.set_major_formatter(
    mdates.DateFormatter("%Y")
)

fig.autofmt_xdate()

plt.tight_layout()
plt.show()


# ==========================================================
# 5. UNEMPLOYMENT DATA INCLUDING 2020
# ==========================================================

df_ue_2020 = pd.read_csv(
    "UE Benefits Search vs UE Rate 2004-20.csv"
)

df_ue_2020["MONTH"] = pd.to_datetime(
    df_ue_2020["MONTH"]
)

print("\n2020 Unemployment Dataset:")
print(df_ue_2020.head())

# Plot 2004-2020
fig, ax1 = plt.subplots(figsize=(14, 8))

ax2 = ax1.twinx()

ax1.set_xlabel("Date")
ax1.set_ylabel("FRED U/E Rate")
ax2.set_ylabel("Search Trend")

ax1.plot(
    df_ue_2020["MONTH"],
    df_ue_2020["UNRATE"],
    linewidth=3
)

ax2.plot(
    df_ue_2020["MONTH"],
    df_ue_2020["UE_BENEFITS_WEB_SEARCH"],
    linewidth=3
)

plt.title(
    'Monthly U.S. "Unemployment Benefits" '
    'Web Search vs UNRATE incl. 2020'
)

ax1.xaxis.set_major_locator(
    mdates.YearLocator()
)

ax1.xaxis.set_major_formatter(
    mdates.DateFormatter("%Y")
)

fig.autofmt_xdate()

plt.tight_layout()
plt.show()