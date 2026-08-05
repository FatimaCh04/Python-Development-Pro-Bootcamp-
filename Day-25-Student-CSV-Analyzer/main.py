import pandas as pd

# Read CSV file
data = pd.read_csv("students.csv")

print("===== Student Data =====")
print(data)

print("\n===== Basic Statistics =====")
print(f"Total Students : {len(data)}")
print(f"Average Marks  : {data['Marks'].mean():.2f}")
print(f"Highest Marks  : {data['Marks'].max()}")
print(f"Lowest Marks   : {data['Marks'].min()}")

topper = data[data["Marks"] == data["Marks"].max()]

print("\n===== Top Performer =====")
print(topper)

search = input("\nEnter student name to search: ").strip()

result = data[data["Name"].str.lower() == search.lower()]

if not result.empty:
    print("\nStudent Found:")
    print(result)
else:
    print("Student not found.")