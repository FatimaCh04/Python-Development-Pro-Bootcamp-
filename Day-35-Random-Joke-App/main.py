import requests


API_URL = "https://official-joke-api.appspot.com/random_joke"


def get_random_joke():
    try:
        response = requests.get(API_URL, timeout=10)

        # Raise an error for bad status codes
        response.raise_for_status()

        data = response.json()

        print("\n😂 Random Programming Joke")
        print("-" * 40)
        print(data["setup"])
        input("\nPress Enter to reveal the punchline...")
        print(f"\n👉 {data['punchline']}")

    except requests.exceptions.ConnectionError:
        print("❌ No internet connection.")

    except requests.exceptions.Timeout:
        print("⌛ Request timed out.")

    except requests.exceptions.HTTPError as error:
        print(f"HTTP Error: {error}")

    except Exception as error:
        print(f"Unexpected Error: {error}")


def main():
    print("=" * 45)
    print("🤣 Welcome to the Random Joke App")
    print("=" * 45)

    while True:
        get_random_joke()

        again = input("\nDo you want another joke? (y/n): ").lower()

        if again != "y":
            print("\n👋 Thanks for using the Random Joke App!")
            break


if __name__ == "__main__":
    main()