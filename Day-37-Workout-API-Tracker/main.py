import requests
from config import API_TOKEN, USERNAME


API_URL = "https://jsonplaceholder.typicode.com/posts"


def get_exercise_data():
    exercise = input("\nWhat exercise did you do? ").strip()

    if not exercise:
        print("❌ Please enter an exercise.")
        return

    exercise_data = {
        "username": USERNAME,
        "exercise": exercise,
        "duration_min": 30,
        "calories": 150
    }

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            API_URL,
            json=exercise_data,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        print("\n🏋️ Exercise Information")
        print("-" * 40)
        print(f"Exercise   : {data.get('exercise')}")
        print(f"Duration   : {data.get('duration_min')} minutes")
        print(f"Calories   : {data.get('calories')} kcal")
        print(f"User       : {data.get('username')}")
        print(f"API ID     : {data.get('id')}")
        print("-" * 40)
        print("✅ Exercise successfully submitted!")

    except requests.exceptions.ConnectionError:
        print("❌ Internet connection error.")

    except requests.exceptions.Timeout:
        print("⌛ Request timed out.")

    except requests.exceptions.HTTPError as error:
        print(f"❌ API Error: {error}")

    except requests.exceptions.RequestException as error:
        print(f"❌ Request failed: {error}")

    except Exception as error:
        print(f"❌ Unexpected error: {error}")


def main():
    print("=" * 45)
    print("       🏋️ WORKOUT API TRACKER")
    print("=" * 45)

    while True:

        get_exercise_data()

        choice = input(
            "\nDo you want to track another exercise? (y/n): "
        ).strip().lower()

        if choice != "y":
            print("\n👋 Thanks for using Workout API Tracker!")
            break


if __name__ == "__main__":
    main()