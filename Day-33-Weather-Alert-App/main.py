import requests

# ---------------- USER CITY ---------------- #
city = input("Enter your city: ")

# ---------------- API URL ---------------- #
url = f"https://wttr.in/{city}?format=j1"

try:
    response = requests.get(url)
    response.raise_for_status()

    data = response.json()

    current = data["current_condition"][0]

    temperature = current["temp_C"]
    humidity = current["humidity"]
    weather = current["weatherDesc"][0]["value"]
    wind_speed = current["windspeedKmph"]

    print("\n========== WEATHER REPORT ==========")
    print(f"📍 City        : {city.title()}")
    print(f"🌡 Temperature : {temperature} °C")
    print(f"💧 Humidity    : {humidity}%")
    print(f"🌥 Condition   : {weather}")
    print(f"💨 Wind Speed  : {wind_speed} km/h")

except requests.exceptions.RequestException as e:
    print("Error:", e)