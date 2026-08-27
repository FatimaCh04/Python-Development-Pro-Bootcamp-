import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("weekly_learning_data.csv")

print("=== WEEKLY LEARNING DATA ===")
print(df.to_string(index=False))

print("\n=== BASIC STATISTICS ===")
print(df.describe())

# Bar chart
plt.figure(figsize=(9, 5))
plt.bar(df["Day"], df["Study Hours"])
plt.title("Study Hours by Day")
plt.xlabel("Day")
plt.ylabel("Study Hours")
plt.tight_layout()
plt.show()

# Line chart
plt.figure(figsize=(9, 5))
plt.plot(df["Day"], df["Coding Hours"], marker="o")
plt.title("Coding Hours Throughout the Week")
plt.xlabel("Day")
plt.ylabel("Coding Hours")
plt.grid(True, alpha=0.25)
plt.tight_layout()
plt.show()

# Comparison bar chart
x = range(len(df))
plt.figure(figsize=(9, 5))
plt.bar([i - 0.2 for i in x], df["Study Hours"], width=0.4, label="Study")
plt.bar([i + 0.2 for i in x], df["Coding Hours"], width=0.4, label="Coding")
plt.xticks(list(x), df["Day"])
plt.title("Study vs Coding Hours")
plt.xlabel("Day")
plt.ylabel("Hours")
plt.legend()
plt.tight_layout()
plt.show()

# Scatter plot
plt.figure(figsize=(8, 5))
plt.scatter(df["Study Hours"], df["Coding Hours"], s=90)
plt.title("Study Hours vs Coding Hours")
plt.xlabel("Study Hours")
plt.ylabel("Coding Hours")
plt.grid(True, alpha=0.25)
plt.tight_layout()
plt.show()

# Pie chart
plt.figure(figsize=(7, 7))
plt.pie(df["Exercises"], labels=df["Day"], autopct="%1.1f%%")
plt.title("Exercise Distribution Across the Week")
plt.tight_layout()
plt.show()

print("\n=== INSIGHTS ===")
print(f"Highest study day: {df.loc[df['Study Hours'].idxmax(), 'Day']}")
print(f"Highest coding day: {df.loc[df['Coding Hours'].idxmax(), 'Day']}")
print(f"Average study hours: {df['Study Hours'].mean():.2f}")
print(f"Average coding hours: {df['Coding Hours'].mean():.2f}")
print(f"Total study hours: {df['Study Hours'].sum():.1f}")
print(f"Total coding hours: {df['Coding Hours'].sum():.1f}")
