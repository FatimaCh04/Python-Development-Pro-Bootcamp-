import pandas as pd
import matplotlib.pyplot as plt

# --------------------------------------------------
# Day 73 - Aggregate & Merge Data with Pandas
# Project: College Major vs Salary
# --------------------------------------------------

# Read the CSV file
df = pd.read_csv("salaries_by_college_major.csv")

# Display the first 5 rows
print("\nFirst 5 rows:")
print(df.head())

# Display information about the dataset
print("\nDataset Information:")
print(df.info())

# Check the number of rows and columns
print("\nShape of Dataset:")
print(df.shape)

# Check for missing values
print("\nMissing Values:")
print(df.isna().sum())

# --------------------------------------------------
# Remove rows with missing values
# --------------------------------------------------

clean_df = df.dropna()

print("\nDataset after removing missing values:")
print(clean_df.head())

# --------------------------------------------------
# Highest Starting Salary
# --------------------------------------------------

highest_starting_salary = clean_df["Starting Median Salary"].max()

print("\nHighest Starting Salary:")
print(highest_starting_salary)

# Find the row with the highest starting salary
highest_starting_salary_row = clean_df[
    clean_df["Starting Median Salary"] == highest_starting_salary
]

print("\nMajor with the highest starting salary:")
print(highest_starting_salary_row[["Undergraduate Major", "Starting Median Salary"]])

# --------------------------------------------------
# Highest Mid-Career Salary
# --------------------------------------------------

highest_midcareer_salary = clean_df["Mid-Career Median Salary"].max()

print("\nHighest Mid-Career Salary:")
print(highest_midcareer_salary)

highest_midcareer_salary_row = clean_df[
    clean_df["Mid-Career Median Salary"] == highest_midcareer_salary
]

print("\nMajor with the highest mid-career salary:")
print(
    highest_midcareer_salary_row[
        ["Undergraduate Major", "Mid-Career Median Salary"]
    ]
)

# --------------------------------------------------
# Lowest Starting Salary
# --------------------------------------------------

lowest_starting_salary = clean_df["Starting Median Salary"].min()

print("\nLowest Starting Salary:")
print(lowest_starting_salary)

lowest_starting_salary_row = clean_df[
    clean_df["Starting Median Salary"] == lowest_starting_salary
]

print("\nMajor with the lowest starting salary:")
print(
    lowest_starting_salary_row[
        ["Undergraduate Major", "Starting Median Salary"]
    ]
)

# --------------------------------------------------
# Lowest Mid-Career Salary
# --------------------------------------------------

lowest_midcareer_salary = clean_df["Mid-Career Median Salary"].min()

print("\nLowest Mid-Career Salary:")
print(lowest_midcareer_salary)

lowest_midcareer_salary_row = clean_df[
    clean_df["Mid-Career Median Salary"] == lowest_midcareer_salary
]

print("\nMajor with the lowest mid-career salary:")
print(
    lowest_midcareer_salary_row[
        ["Undergraduate Major", "Mid-Career Median Salary"]
    ]
)

# --------------------------------------------------
# College Major with Highest Salary Potential
# --------------------------------------------------

clean_df["Salary Increase"] = (
    clean_df["Mid-Career Median Salary"]
    - clean_df["Starting Median Salary"]
)

highest_salary_increase = clean_df["Salary Increase"].max()

print("\nHighest salary increase:")
print(highest_salary_increase)

highest_salary_increase_row = clean_df[
    clean_df["Salary Increase"] == highest_salary_increase
]

print("\nMajor with the highest salary increase:")
print(
    highest_salary_increase_row[
        [
            "Undergraduate Major",
            "Starting Median Salary",
            "Mid-Career Median Salary",
            "Salary Increase",
        ]
    ]
)

# --------------------------------------------------
# Lowest Salary Increase
# --------------------------------------------------

lowest_salary_increase = clean_df["Salary Increase"].min()

print("\nLowest salary increase:")
print(lowest_salary_increase)

lowest_salary_increase_row = clean_df[
    clean_df["Salary Increase"] == lowest_salary_increase
]

print("\nMajor with the lowest salary increase:")
print(
    lowest_salary_increase_row[
        [
            "Undergraduate Major",
            "Starting Median Salary",
            "Mid-Career Median Salary",
            "Salary Increase",
        ]
    ]
)

# --------------------------------------------------
# Top 10 Majors by Salary Increase
# --------------------------------------------------

top_10 = clean_df.sort_values(
    by="Salary Increase",
    ascending=False
).head(10)

print("\nTop 10 majors by salary increase:")
print(
    top_10[
        [
            "Undergraduate Major",
            "Starting Median Salary",
            "Mid-Career Median Salary",
            "Salary Increase",
        ]
    ]
)

# --------------------------------------------------
# Visualization
# --------------------------------------------------

plt.figure(figsize=(12, 7))

plt.bar(
    top_10["Undergraduate Major"],
    top_10["Salary Increase"]
)

plt.title("Top 10 College Majors by Salary Increase")
plt.xlabel("College Major")
plt.ylabel("Salary Increase ($)")
plt.xticks(rotation=45, ha="right")

plt.tight_layout()
plt.show()