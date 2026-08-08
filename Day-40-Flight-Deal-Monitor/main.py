import requests


API_URL = "https://jsonplaceholder.typicode.com/posts"


def search_flights(origin, destination):
    """Simulate a flight search using a demo REST API."""

    flight_request = {
        "origin": origin,
        "destination": destination,
        "status": "available"
    }

    try:
        response = requests.post(
            API_URL,
            json=flight_request,
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except requests.exceptions.ConnectionError:
        print("❌ Internet connection error.")
        return None

    except requests.exceptions.Timeout:
        print("⌛ Request timed out.")
        return None

    except requests.exceptions.HTTPError as error:
        print(f"❌ HTTP Error: {error}")
        return None

    except requests.exceptions.RequestException as error:
        print(f"❌ Request failed: {error}")
        return None


def display_flight_deal(result, origin, destination):
    """Display the simulated flight deal."""

    print("\n" + "=" * 60)
    print("✈️ FLIGHT DEAL FOUND")
    print("=" * 60)

    print(f"Departure Airport : {origin}")
    print(f"Arrival Airport   : {destination}")
    print("Airline           : Demo Airways")
    print("Flight Status     : Available")
    print("Price             : $299")
    print(f"Deal ID           : {result.get('id')}")

    print("-" * 60)
    print("🎉 This is a practice flight deal.")
    print("=" * 60)


def main():

    print("=" * 60)
    print("       ✈️ AUTOMATED FLIGHT DEAL MONITOR")
    print("=" * 60)

    origin = input(
        "\nEnter departure airport IATA code: "
    ).strip().upper()

    destination = input(
        "Enter arrival airport IATA code: "
    ).strip().upper()

    # Validate IATA codes
    if len(origin) != 3 or not origin.isalpha():
        print("\n❌ Departure code must contain exactly 3 letters.")
        return

    if len(destination) != 3 or not destination.isalpha():
        print("\n❌ Arrival code must contain exactly 3 letters.")
        return

    print(f"\n🔎 Monitoring route: {origin} → {destination}")

    result = search_flights(origin, destination)

    if result is None:
        print("\n❌ Could not complete flight search.")
        return

    display_flight_deal(
        result,
        origin,
        destination
    )

    print("\n✅ Flight deal monitoring completed.")


if __name__ == "__main__":
    main()