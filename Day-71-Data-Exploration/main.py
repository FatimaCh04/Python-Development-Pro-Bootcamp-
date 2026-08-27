import pandas as pd

DATA_FILE = "college_major_salaries.csv"


def main():
    # ---------------------------------------------------------
    # DAY 71 - DATA EXPLORATION WITH PANDAS
    # ---------------------------------------------------------

    df = pd.read_csv(DATA_FILE)

    print("\n=== DATASET ===")
    print(df)

    print("\n=== FIRST 5 ROWS ===")
    print(df.head())

    print("\n=== LAST 5 ROWS ===")
    print(df.tail())

    print("\n=== COLUMN NAMES ===")
    print(df.columns.tolist())

    print("\n=== DATASET SHAPE ===")
    print(f"Rows: {df.shape[0]}")
    print(f"Columns: {df.shape[1]}")

    print("\n=== DATA TYPES ===")
    print(df.dtypes)

    print("\n=== BASIC STATISTICS ===")
    print(df.describe())

    print("\n=== MISSING VALUES ===")
    print(df.isnull().sum())

    # ---------------------------------------------------------
    # SALARY EXPLORATION
    # ---------------------------------------------------------

    print("\n=== TOP 5 MAJORS BY STARTING SALARY ===")
    print(
        df.sort_values(
            by="Starting Median Salary",
            ascending=False
        )[["Major", "Starting Median Salary"]].head()
    )

    print("\n=== TOP 5 MAJORS BY MID-CAREER SALARY ===")
    print(
        df.sort_values(
            by="Mid-Career Median Salary",
            ascending=False
        )[["Major", "Mid-Career Median Salary"]].head()
    )

    # Create a useful calculated column.
    df["Salary Increase"] = (
        df["Mid-Career Median Salary"]
        - df["Starting Median Salary"]
    )

    print("\n=== LARGEST SALARY INCREASE ===")
    print(
        df.sort_values(
            by="Salary Increase",
            ascending=False
        )[[
            "Major",
            "Starting Median Salary",
            "Mid-Career Median Salary",
            "Salary Increase"
        ]].head()
    )

    print("\n=== LOWEST STARTING SALARIES ===")
    print(
        df.sort_values(
            by="Starting Median Salary"
        )[["Major", "Starting Median Salary"]].head()
    )

    print("\n=== LOWEST UNEMPLOYMENT RATES ===")
    print(
        df.sort_values(
            by="Unemployment Rate"
        )[["Major", "Unemployment Rate"]].head()
    )

    print("\n=== HIGHEST UNEMPLOYMENT RATES ===")
    print(
        df.sort_values(
            by="Unemployment Rate",
            ascending=False
        )[["Major", "Unemployment Rate"]].head()
    )

    # ---------------------------------------------------------
    # FILTERING
    # ---------------------------------------------------------

    high_salary = df[
        df["Mid-Career Median Salary"] >= 80000
    ]

    print("\n=== MAJORS WITH MID-CAREER SALARY >= $80,000 ===")
    print(
        high_salary[
            ["Major", "Mid-Career Median Salary"]
        ]
    )

    # ---------------------------------------------------------
    # AVERAGES
    # ---------------------------------------------------------

    print("\n=== AVERAGES ===")
    print(
        f"Average starting salary: "
        f"${df['Starting Median Salary'].mean():,.0f}"
    )

    print(
        f"Average mid-career salary: "
        f"${df['Mid-Career Median Salary'].mean():,.0f}"
    )

    print(
        f"Average unemployment rate: "
        f"{df['Unemployment Rate'].mean():.2%}"
    )


if __name__ == "__main__":
    main()
