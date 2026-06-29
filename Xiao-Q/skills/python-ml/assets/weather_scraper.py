"""
Weather Scraper - Complete Example
Fetches weather information using wttr.in (no API key required).
"""

import requests


def get_weather_simple(city):
    """
    Get a simple one-line weather report for a city.

    Args:
        city: Name of the city (English name works best).
    """
    url = f"https://wttr.in/{city}?format=3"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        print(response.text.strip())
    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather: {e}")


def get_weather_detail(city):
    """
    Get detailed weather information for a city.

    Args:
        city: Name of the city.
    """
    url = f"https://wttr.in/{city}?format=j1"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        current = data["current_condition"][0]
        temp_c = current["temp_C"]
        feels_like = current["FeelsLikeC"]
        desc = current["weatherDesc"][0]["value"]
        humidity = current["humidity"]
        wind_kmph = current["windspeedKmph"]

        print(f"\n=== Weather in {city} ===")
        print(f"Description : {desc}")
        print(f"Temperature  : {temp_c} C")
        print(f"Feels like   : {feels_like} C")
        print(f"Humidity     : {humidity}%")
        print(f"Wind speed   : {wind_kmph} km/h")

        # Show multi-day forecast
        print("\n--- Forecast ---")
        for day in data["weather"]:
            date = day["date"]
            max_temp = day["maxtempC"]
            min_temp = day["mintempC"]
            desc_day = day["hourly"][4]["weatherDesc"][0]["value"]
            print(f"{date}: {desc_day}, {min_temp}C ~ {max_temp}C")

    except requests.exceptions.RequestException as e:
        print(f"Error fetching weather: {e}")
    except KeyError:
        print("Unexpected response format. Please check the city name.")


def main():
    """Main program loop."""
    print("=== Weather Query Tool ===")
    print("(Using wttr.in - no API key needed)")
    while True:
        city = input("\nEnter city name (or 'quit' to exit): ").strip()
        if city.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        if not city:
            continue
        get_weather_simple(city)
        # Uncomment below to show detailed info:
        # get_weather_detail(city)


if __name__ == "__main__":
    main()
