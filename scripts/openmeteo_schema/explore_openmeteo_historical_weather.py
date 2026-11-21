import requests
import pprint
import pandas as pd


url = "https://archive-api.open-meteo.com/v1/archive"
params = {
	"latitude": 24.8608,
	"longitude": 67.0104,
	"hourly": ["temperature_2m", "relative_humidity_2m", "precipitation", "wind_speed_10m", "wind_direction_10m"],
    "start_date": "2025-11-21",
	"end_date": "2026-11-15",
    "timezone":"UTC",
}

response = requests.get(url = url, params =params ,timeout=15)
response.raise_for_status()
json_response = response.json()

print(json_response["hourly_units"])

df = pd.DataFrame(json_response["hourly"])

df['time'] = pd.to_datetime(df['time'],utc = True)

print(df.dtypes)

print(df.head(3))

print(len(df))

print(df.isna().mean()*100)

