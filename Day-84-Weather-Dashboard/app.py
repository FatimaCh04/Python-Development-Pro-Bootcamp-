import os
import requests

from flask import Flask, render_template, request
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

app = Flask(__name__)

API_KEY = os.getenv("OPENWEATHER_API_KEY")

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"


@app.route("/", methods=["GET", "POST"])
def index():

    weather = None
    error = None
    city = ""

    if request.method == "POST":

        city = request.form.get("city", "").strip()

        if not city:
            error = "Please enter a city name."

        elif not API_KEY:
            error = (
                "Weather API key is not configured. "
                "Please add OPENWEATHER_API_KEY to your .env file."
            )

        else:

            params = {
                "q": city,
                "appid": API_KEY,
                "units": "metric"
            }

            try:

                response = requests.get(
                    BASE_URL,
                    params=params,
                    timeout=10
                )

                if response.status_code == 404:
                    error = "City not found. Please check the city name."

                elif response.status_code == 401:
                    error = "Invalid Weather API key."

                elif response.status_code != 200:
                    error = "Unable to retrieve weather data."

                else:

                    data = response.json()

                    weather = {
                        "city": data["name"],
                        "country": data["sys"]["country"],
                        "temperature": round(data["main"]["temp"]),
                        "feels_like": round(data["main"]["feels_like"]),
                        "humidity": data["main"]["humidity"],
                        "pressure": data["main"]["pressure"],
                        "wind_speed": round(
                            data["wind"]["speed"] * 3.6,
                            1
                        ),
                        "description": data["weather"][0]["description"].title(),
                        "icon": data["weather"][0]["icon"],
                        "sunrise": format_time(
                            data["sys"]["sunrise"]
                        ),
                        "sunset": format_time(
                            data["sys"]["sunset"]
                        )
                    }

            except requests.exceptions.Timeout:
                error = "Weather service timed out. Please try again."

            except requests.exceptions.ConnectionError:
                error = "Could not connect to the weather service."

            except requests.exceptions.RequestException:
                error = "An error occurred while fetching weather data."

    return render_template(
        "index.html",
        weather=weather,
        error=error,
        city=city
    )


def format_time(timestamp):
    """Convert Unix timestamp to readable time."""

    from datetime import datetime

    return datetime.fromtimestamp(timestamp).strftime("%I:%M %p")


if __name__ == "__main__":
    app.run(debug=True)