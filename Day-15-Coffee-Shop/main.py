MENU = {
    "espresso": {"water": 50, "milk": 0, "coffee": 18, "price": 2.0},
    "latte": {"water": 200, "milk": 150, "coffee": 24, "price": 3.5},
    "cappuccino": {"water": 250, "milk": 100, "coffee": 24, "price": 4.0},
}

resources = {
    "water": 500,
    "milk": 300,
    "coffee": 100,
}

profit = 0.0


def report():
    print("\n------ Coffee Shop Report ------")
    print(f"Water : {resources['water']}ml")
    print(f"Milk  : {resources['milk']}ml")
    print(f"Coffee: {resources['coffee']}g")
    print(f"Profit: ${profit:.2f}")


def enough_resources(drink):
    ingredients = MENU[drink]

    for item in ["water", "milk", "coffee"]:
        if resources[item] < ingredients[item]:
            print(f"Sorry! Not enough {item}.")
            return False
    return True


def process_payment(cost):
    print(f"\nThis drink costs ${cost}")

    paid = float(input("Enter payment: $"))

    if paid < cost:
        print("Sorry! Not enough money. Refunded.")
        return False

    change = paid - cost

    if change > 0:
        print(f"Change: ${change:.2f}")

    return True


def make_coffee(drink):
    global profit

    ingredients = MENU[drink]

    for item in ["water", "milk", "coffee"]:
        resources[item] -= ingredients[item]

    profit += ingredients["price"]

    print(f"\n☕ Here is your {drink}. Enjoy!\n")


machine_on = True

print("☕ Welcome to Python Coffee Shop!")

while machine_on:

    choice = input(
        "What would you like? (espresso/latte/cappuccino/report/off): "
    ).lower()

    if choice == "off":
        machine_on = False
        print("Coffee machine turned off.")

    elif choice == "report":
        report()

    elif choice in MENU:

        if enough_resources(choice):

            if process_payment(MENU[choice]["price"]):
                make_coffee(choice)

    else:
        print("Invalid option.")