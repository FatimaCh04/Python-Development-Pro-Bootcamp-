import random

print("🐞 Debugging Practice Program")
print("-" * 35)

# 1. Random Number
random_number = random.randint(1, 10)
print(f"Random Number: {random_number}")

# 2. List Index
fruits = ["Apple", "Banana", "Orange", "Mango"]

print("\nFruit List:")
for fruit in fruits:
    print(fruit)

# 3. Dictionary Access
student = {
    "name": "Fatima",
    "age": 21,
    "course": "Python"
}

print("\nStudent Information")
print(f"Name : {student['name']}")
print(f"Age  : {student['age']}")
print(f"Course : {student['course']}")

# 4. Even or Odd
number = int(input("\nEnter any number: "))

if number % 2 == 0:
    print("Even Number")
else:
    print("Odd Number")

# 5. Average Marks
marks = [85, 92, 78, 90, 88]

average = sum(marks) / len(marks)

print("\nMarks:", marks)
print("Average:", average)

print("\n✅ Program Finished Successfully!")