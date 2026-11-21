import requests 
import pprint

url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 24.8608,
	"longitude": 67.0104,
	"hourly": ["temperature_2m","relative_humidity_2m", "precipitation", "precipitation_probability", "uv_index","wind_speed_10m" ,"wind_direction_10m"],
    "past_days":7,
    "forecast_days":1,
    "timezone":"UTC",
}

resp = requests.get(url = url, params = params)
data = resp.json()
print(list(data.keys()))

# pprint.pprint(data)
hourly_unit = data["hourly_units"]
print("hourly_units:",list(hourly_unit.keys()))

wind_speed_10m = hourly_unit["wind_speed_10m"]
print("wind_speed_10m:",wind_speed_10m)


