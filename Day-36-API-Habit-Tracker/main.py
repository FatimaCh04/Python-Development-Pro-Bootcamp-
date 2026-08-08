import requests
from config import API_TOKEN, USERNAME

BASE_URL = "https://jsonplaceholder.typicode.com"


def check_api_connection():
    """Check whether the demo API is reachable."""

    try:
        response = requests.get(
            f"{BASE_URL}/posts/1",
            timeout=10
        )

        response.raise_for_status()

        print("✅ API connection successful!")
        return True

    except requests.exceptions.ConnectionError:
        print("❌ Internet connection error.")
        return False

    except requests.exceptions.Timeout:
        print("⌛ Request timed out.")
        return False

    except requests.exceptions.HTTPError as error:
        print(f"❌ HTTP Error: {error}")
        return False


def create_habit():
    """Send habit data using a POST request."""

    habit_name = input("Enter your habit: ").strip()

    if not habit_name:
        print("❌ Habit name cannot be empty.")
        return

    habit_data = {
        "username": USERNAME,
        "habit": habit_name,
        "status": "completed"
    }

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/posts",
            json=habit_data,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        result = response.json()

        print("\n🎉 Habit submitted successfully!")
        print(f"ID       : {result.get('id')}")
        print(f"Username : {result.get('username')}")
        print(f"Habit    : {result.get('habit')}")
        print(f"Status   : {result.get('status')}")

    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API.")

    except requests.exceptions.Timeout:
        print("⌛ API request timed out.")

    except requests.exceptions.HTTPError as error:
        print(f"❌ HTTP Error: {error}")

    except requests.exceptions.RequestException as error:
        print(f"❌ Request failed: {error}")

    except Exception as error:
        print(f"❌ Unexpected error: {error}")


def main():
    print("=" * 45)
    print("        🚀 API HABIT TRACKER")
    print("=" * 45)

    if not API_TOKEN or not USERNAME:
        print("\n⚠️ API credentials are missing.")
        print("Please check your .env file.")
        return

    if not check_api_connection():
        return

    print("\n1. Create Habit")
    print("2. Exit")

    choice = input("\nChoose an option: ").strip()

    if choice == "1":
        create_habit()

    elif choice == "2":
        print("👋 Goodbye!")

    else:
        print("❌ Invalid option.")


if __name__ == "__main__":
    main()