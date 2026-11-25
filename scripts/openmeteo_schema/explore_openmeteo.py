import requests
import pprint
import pandas as pd


# Make sure all required weather variables are listed here
# The order of variables in hourly or daily is important to assign them correctly below
url = "https://api.open-meteo.com/v1/forecast"
params = {
	"latitude": 24.8608,
	"longitude": 67.0104,
	"hourly": ["temperature_2m","relative_humidity_2m", "precipitation", "precipitation_probability", "uv_index","wind_speed_10m" ,"wind_direction_10m"],
    "past_days":7,
    "forecast_days":1,
    "timezone":"UTC",
}


response = requests.get(url = url, params =params ,timeout=15)
response.raise_for_status()
json_response = response.json()

#print(list(json_response.keys()))
#['latitude', 'longitude', 'generationtime_ms', 'utc_offset_seconds', 'timezone', 'timezone_abbreviation', 'elevation', 'hourly_units', 'hourly']

#print(json_response["hourly_units"])
#{'time': 'iso8601', 'temperature_2m': '°C', 'relative_humidity_2m': '%', 'precipitation': 'mm', 'precipitation_probability': '%', 'uv_index': '', 'wind_speed_10m': 'km/h', 'wind_direction_10m': '°'}

df = pd.DataFrame(json_response["hourly"])

print("--------before utc:-----------")

print(df.head(3))

print("df.dtypes\n",df.dtypes)

df['time'] = pd.to_datetime(df['time'],utc = True)


print("--------after utc:-----------")

print(df.head(3))

print("df.dtypes:\n",df.dtypes)

print("\ndf.isna().mean():\n",df.isna().mean() *100)




