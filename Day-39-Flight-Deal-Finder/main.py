import requests


API_URL = "https://jsonplaceholder.typicode.com/posts"


def search_flights(departure, arrival):
    """Send a flight search request to a demo API."""

    flight_data = {
        "departure": departure.upper(),
        "arrival": arrival.upper()
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(
            API_URL,
            json=flight_data,
            headers=headers,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        return data

    except requests.exceptions.ConnectionError:
        print("\n❌ Internet connection error.")
        return None

    except requests.exceptions.Timeout:
        print("\n⌛ Request timed out.")
        return None

    except requests.exceptions.HTTPError as error:
        print(f"\n❌ HTTP Error: {error}")
        return None

    except requests.exceptions.RequestException as error:
        print(f"\n❌ Request failed: {error}")
        return None


def main():

    print("=" * 50)
    print("       ✈️ FLIGHT DEAL FINDER")
    print("=" * 50)

    departure = input(
        "\nEnter departure airport IATA code: "
    ).strip().upper()

    arrival = input(
        "Enter arrival airport IATA code: "
    ).strip().upper()

    if len(departure) != 3 or not departure.isalpha():
        print("\n❌ Departure code must contain 3 letters.")
        return

    if len(arrival) != 3 or not arrival.isalpha():
        print("\n❌ Arrival code must contain 3 letters.")
        return

    print("\n🔎 Searching for flights...")

    result = search_flights(departure, arrival)

    if result is None:
        return

    print("\n✈️ Flight Search Result")
    print("=" * 50)

    print(f"Departure : {result.get('departure')}")
    print(f"Arrival   : {result.get('arrival')}")
    print(f"Search ID : {result.get('id')}")

    print("\n✅ Flight search completed successfully!")


if __name__ == "__main__":
    main()