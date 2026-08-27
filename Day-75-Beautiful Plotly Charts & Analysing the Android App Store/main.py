import pandas as pd
import plotly.express as px


# ============================================================
# DAY 75
# Beautiful Plotly Charts & Analysing the Android App Store
# ============================================================

# ------------------------------------------------------------
# 1. Load the dataset
# ------------------------------------------------------------

df = pd.read_csv("apps.csv")

print("\nFirst 5 rows:")
print(df.head())

print("\nDataset shape:")
print(df.shape)

print("\nDataset information:")
print(df.info())

print("\nMissing values:")
print(df.isna().sum())


# ------------------------------------------------------------
# 2. Clean the data
# ------------------------------------------------------------

# Remove duplicate apps
df = df.drop_duplicates(subset="App")

# Convert Rating to numeric
df["Rating"] = pd.to_numeric(
    df["Rating"],
    errors="coerce"
)

# Convert Reviews to numeric
df["Reviews"] = pd.to_numeric(
    df["Reviews"],
    errors="coerce"
)

# Convert Installs to numeric
df["Installs"] = (
    df["Installs"]
    .astype(str)
    .str.replace(",", "", regex=False)
    .str.replace("+", "", regex=False)
)

df["Installs"] = pd.to_numeric(
    df["Installs"],
    errors="coerce"
)

# Convert Price to numeric
df["Price"] = (
    df["Price"]
    .astype(str)
    .str.replace("$", "", regex=False)
)

df["Price"] = pd.to_numeric(
    df["Price"],
    errors="coerce"
)

# Remove rows without important values
df = df.dropna(
    subset=[
        "Rating",
        "Reviews",
        "Installs"
    ]
)

print("\nCleaned dataset:")
print(df.head())


# ============================================================
# 3. Most Popular App Categories
# ============================================================

category_count = (
    df["Category"]
    .value_counts()
    .reset_index()
)

category_count.columns = [
    "Category",
    "Number of Apps"
]

print("\nTop App Categories:")
print(category_count.head(10))


# Plotly Bar Chart
fig = px.bar(
    category_count.head(15),
    x="Category",
    y="Number of Apps",
    title="Most Popular App Categories"
)

fig.update_layout(
    xaxis_title="Category",
    yaxis_title="Number of Apps",
    xaxis_tickangle=-45
)

fig.show()


# ============================================================
# 4. App Rating Distribution
# ============================================================

fig = px.histogram(
    df,
    x="Rating",
    nbins=20,
    title="Distribution of App Ratings"
)

fig.update_layout(
    xaxis_title="Rating",
    yaxis_title="Number of Apps"
)

fig.show()


# ============================================================
# 5. Average Rating by Category
# ============================================================

average_rating = (
    df.groupby("Category")["Rating"]
    .mean()
    .sort_values(ascending=False)
    .reset_index()
)

print("\nHighest Rated Categories:")
print(average_rating.head(10))


fig = px.bar(
    average_rating.head(15),
    x="Category",
    y="Rating",
    title="Average Rating by App Category"
)

fig.update_layout(
    xaxis_title="Category",
    yaxis_title="Average Rating",
    xaxis_tickangle=-45
)

fig.show()


# ============================================================
# 6. Reviews vs Rating
# ============================================================

fig = px.scatter(
    df,
    x="Reviews",
    y="Rating",
    size="Installs",
    hover_name="App",
    log_x=True,
    title="App Reviews vs Rating"
)

fig.update_layout(
    xaxis_title="Number of Reviews",
    yaxis_title="Rating"
)

fig.show()


# ============================================================
# 7. Free vs Paid Apps
# ============================================================

if "Type" in df.columns:

    app_type = (
        df["Type"]
        .value_counts()
        .reset_index()
    )

    app_type.columns = [
        "Type",
        "Number of Apps"
    ]

    print("\nFree vs Paid Apps:")
    print(app_type)

    fig = px.pie(
        app_type,
        names="Type",
        values="Number of Apps",
        hole=0.35,
        title="Free vs Paid Apps"
    )

    fig.show()


# ============================================================
# 8. Content Rating Distribution
# ============================================================

if "Content Rating" in df.columns:

    content_rating = (
        df["Content Rating"]
        .value_counts()
        .reset_index()
    )

    content_rating.columns = [
        "Content Rating",
        "Number of Apps"
    ]

    fig = px.bar(
        content_rating,
        x="Content Rating",
        y="Number of Apps",
        title="Apps by Content Rating"
    )

    fig.show()


# ============================================================
# 9. Most Reviewed Apps
# ============================================================

most_reviewed = (
    df.sort_values(
        "Reviews",
        ascending=False
    )
    .head(10)
)

print("\nTop 10 Most Reviewed Apps:")
print(
    most_reviewed[
        [
            "App",
            "Reviews",
            "Rating"
        ]
    ]
)


# ============================================================
# 10. Most Installed Apps
# ============================================================

most_installed = (
    df.sort_values(
        "Installs",
        ascending=False
    )
    .head(10)
)

print("\nTop 10 Most Installed Apps:")
print(
    most_installed[
        [
            "App",
            "Installs",
            "Rating"
        ]
    ]
)


# ============================================================
# 11. Price Analysis
# ============================================================

paid_apps = df[df["Price"] > 0]

print("\nNumber of paid apps:")
print(len(paid_apps))

if not paid_apps.empty:

    print("\nMost expensive apps:")
    print(
        paid_apps.sort_values(
            "Price",
            ascending=False
        )[
            [
                "App",
                "Price",
                "Rating"
            ]
        ].head(10)
    )

    fig = px.histogram(
        paid_apps,
        x="Price",
        nbins=30,
        title="Distribution of Paid App Prices"
    )

    fig.update_layout(
        xaxis_title="Price ($)",
        yaxis_title="Number of Apps"
    )

    fig.show()


# ============================================================
# 12. Category vs Reviews
# ============================================================

category_reviews = (
    df.groupby("Category")["Reviews"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

fig = px.bar(
    category_reviews.head(15),
    x="Category",
    y="Reviews",
    title="Total Reviews by App Category"
)

fig.update_layout(
    xaxis_title="Category",
    yaxis_title="Total Reviews",
    xaxis_tickangle=-45
)

fig.show()


print("\n======================================")
print("Day 75 Analysis Completed Successfully!")
print("======================================")