import requests
from datetime import datetime


# ============================================================
# DAY 77 - HABIT TRACKER
# Angela Yu - 100 Days of Code
# ============================================================

# ------------------------------------------------------------
# YOUR PIXELA ACCOUNT DETAILS
# ------------------------------------------------------------

USERNAME = "fatima123"
TOKEN = "abc123xyz"
GRAPH_ID = "coding"

pixela_endpoint = "https://pixe.la/v1/users"

headers = {
    "X-USER-TOKEN": TOKEN
}


# ============================================================
# 1. CREATE PIXELA USER
# ============================================================

def create_user():
    user_params = {
        "token": TOKEN,
        "username": USERNAME,
        "agreeTermsOfService": "yes",
        "notMinor": "yes"
    }

    response = requests.post(
        url=pixela_endpoint,
        json=user_params
    )

    print("\nCREATE USER")
    print(response.status_code)
    print(response.text)


# ============================================================
# 2. CREATE GRAPH
# ============================================================

def create_graph():
    graph_endpoint = (
        f"{pixela_endpoint}/{USERNAME}/graphs"
    )

    graph_config = {
        "id": GRAPH_ID,
        "name": "Coding Habit",
        "unit": "hours",
        "type": "float",
        "color": "ajisai"
    }

    response = requests.post(
        url=graph_endpoint,
        json=graph_config,
        headers=headers
    )

    print("\nCREATE GRAPH")
    print(response.status_code)
    print(response.text)


# ============================================================
# 3. ADD PIXEL
# ============================================================

def add_pixel(quantity):
    pixel_endpoint = (
        f"{pixela_endpoint}/{USERNAME}"
        f"/graphs/{GRAPH_ID}"
    )

    today = datetime.now()

    pixel_data = {
        "date": today.strftime("%Y%m%d"),
        "quantity": str(quantity)
    }

    response = requests.post(
        url=pixel_endpoint,
        json=pixel_data,
        headers=headers
    )

    print("\nADD PIXEL")
    print(response.status_code)
    print(response.text)


# ============================================================
# 4. UPDATE PIXEL
# ============================================================

def update_pixel(quantity):
    today = datetime.now()

    date = today.strftime("%Y%m%d")

    update_endpoint = (
        f"{pixela_endpoint}/{USERNAME}"
        f"/graphs/{GRAPH_ID}/{date}"
    )

    update_data = {
        "quantity": str(quantity)
    }

    response = requests.put(
        url=update_endpoint,
        json=update_data,
        headers=headers
    )

    print("\nUPDATE PIXEL")
    print(response.status_code)
    print(response.text)


# ============================================================
# 5. DELETE PIXEL
# ============================================================

def delete_pixel():
    today = datetime.now()

    date = today.strftime("%Y%m%d")

    delete_endpoint = (
        f"{pixela_endpoint}/{USERNAME}"
        f"/graphs/{GRAPH_ID}/{date}"
    )

    response = requests.delete(
        url=delete_endpoint,
        headers=headers
    )

    print("\nDELETE PIXEL")
    print(response.status_code)
    print(response.text)


# ============================================================
# MAIN PROGRAM
# ============================================================

print("========================================")
print("       DAY 77 - HABIT TRACKER")
print("========================================")

print("\n1. Create User")
print("2. Create Graph")
print("3. Add Pixel")
print("4. Update Pixel")
print("5. Delete Pixel")
print("6. Exit")

choice = input("\nChoose an option: ")

if choice == "1":

    create_user()

elif choice == "2":

    create_graph()

elif choice == "3":

    hours = input(
        "\nHow many hours did you code today? "
    )

    try:
        hours = float(hours)
        add_pixel(hours)

    except ValueError:
        print("Please enter a valid number.")

elif choice == "4":

    hours = input(
        "\nEnter the updated coding hours: "
    )

    try:
        hours = float(hours)
        update_pixel(hours)

    except ValueError:
        print("Please enter a valid number.")

elif choice == "5":

    delete_pixel()

elif choice == "6":

    print("Goodbye! 👋")

else:

    print("Invalid choice.")