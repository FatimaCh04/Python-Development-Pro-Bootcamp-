from os import system

# ---------- Logo ----------
logo = r"""
 ___________________________
|                           |
|      PYTHON CALCULATOR    |
|___________________________|
"""


# ---------- Functions ----------
def add(n1, n2):
    return n1 + n2


def subtract(n1, n2):
    return n1 - n2


def multiply(n1, n2):
    return n1 * n2


def divide(n1, n2):
    if n2 == 0:
        return "Cannot divide by zero!"
    return n1 / n2


operations = {
    "+": add,
    "-": subtract,
    "*": multiply,
    "/": divide,
}


def calculator():
    print(logo)

    first_number = float(input("What's the first number? "))

    while True:

        print("\nAvailable operations:")
        for symbol in operations:
            print(symbol)

        operator = input("Pick an operation: ")

        while operator not in operations:
            operator = input("Invalid operator. Pick again: ")

        second_number = float(input("What's the next number? "))

        answer = operations[operator](first_number, second_number)

        print(f"\n{first_number} {operator} {second_number} = {answer}")

        choice = input(
            f"\nType 'y' to continue calculating with {answer}, "
            f"or type 'n' to start a new calculation: "
        ).lower()

        if choice == "y":
            if isinstance(answer, str):
                print("\nCannot continue with an error.")
                break
            first_number = answer

        elif choice == "n":
            system("cls||clear")
            calculator()
            return

        else:
            print("\nCalculator Closed.")
            break


calculator()