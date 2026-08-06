import pandas as pd

# Read CSV file
students = pd.read_csv("students.csv")

print("===== Student Records =====")
print(students)

# List Comprehension
passed_students = [
    name
    for name, marks in zip(students["Name"], students["Marks"])
    if marks >= 70
]

# Dictionary Comprehension
grades = {
    row["Name"]: (
        "A" if row["Marks"] >= 90
        else "B" if row["Marks"] >= 80
        else "C" if row["Marks"] >= 70
        else "Fail"
    )
    for _, row in students.iterrows()
}

print("\n===== Passed Students =====")
for student in passed_students:
    print(student)

print("\n===== Grades =====")
for name, grade in grades.items():
    print(f"{name}: {grade}")

average = students["Marks"].mean()

print(f"\nAverage Marks: {average:.2f}")

topper = students.loc[students["Marks"].idxmax()]

print("\n===== Top Performer =====")
print(f"{topper['Name']} - {topper['Marks']} Marks")