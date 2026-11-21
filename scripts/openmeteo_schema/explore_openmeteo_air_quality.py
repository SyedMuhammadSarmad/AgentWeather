import requests
import pprint
import pandas as pd


url = "https://air-quality-api.open-meteo.com/v1/air-quality"
params = {
	"latitude": 24.8608,
	"longitude": 67.0104,
	"hourly": ["pm10", "pm2_5", "uv_index", "us_aqi"],
    "start_date": "2025-11-21",
	"end_date": "2026-11-21",
    "timezone":"UTC",
}

response = requests.get(url = url, params =params ,timeout=15)
response.raise_for_status()
json_response = response.json()
# print(list(json_response.keys()))
# ['latitude', 'longitude', 'generationtime_ms', 'utc_offset_seconds', 'timezone', 'timezone_abbreviation', 'elevation', 'hourly_units', 'hourly']

print(json_response["hourly_units"])

df = pd.DataFrame(json_response["hourly"])

df['time'] = pd.to_datetime(df['time'],utc = True)

print(df.dtypes)

print(df.head(3))

print(len(df))

print(df.isna().mean() * 100)





