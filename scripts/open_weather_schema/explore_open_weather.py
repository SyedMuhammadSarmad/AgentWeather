from dotenv import load_dotenv
import os,requests
import pandas as pd
from pprint import pprint

load_dotenv()

api_key = os.getenv("OPEN_WEATHER_API_KEY")

url = "https://api.openweathermap.org/data/2.5/air_pollution/history"

params = {
    "lat" : 24.8608,
    "lon" : 67.0104,
    "start" : int(pd.Timestamp("2025-11-21", tz="UTC").timestamp()),
    "end" :  int(pd.Timestamp("2026-11-21", tz="UTC").timestamp()),
    "appid" : api_key,
}

response = requests.get(url = url,params= params,timeout = 15)
response.raise_for_status()
json_response = response.json()

#print(list(json_response.keys()))
#['coord', 'list']

# pprint(json_response['list'])

df = pd.json_normalize(json_response["list"])

df['dt'] = pd.to_datetime(df['dt'],unit="s",utc = True)

print(df.head(3))

print(df.tail(3))

print(df.isna().mean()*100)

'''
weather_schema$ uv run explore_open_weather.py 
                         dt  main.aqi  ...  components.pm10  components.nh3
0 2025-11-21 00:00:00+00:00         3  ...            80.54             0.0
1 2025-11-21 01:00:00+00:00         3  ...            84.31             0.0
2 2025-11-21 02:00:00+00:00         3  ...            88.31             0.0

[3 rows x 10 columns]
                            dt  main.aqi  ...  components.pm10  components.nh3
8302 2026-11-20 22:00:00+00:00         3  ...            97.62            1.26
8303 2026-11-20 23:00:00+00:00         3  ...            97.88            1.36
8304 2026-11-21 00:00:00+00:00         3  ...            98.75            1.50

[3 rows x 10 columns]
dt                  0.0
main.aqi            0.0
components.co       0.0
components.no       0.0
components.no2      0.0
components.o3       0.0
components.so2      0.0
components.pm2_5    0.0
components.pm10     0.0
components.nh3      0.0

A full year (2025-11-21 to 2026-11-21) has 365 × 24 + 1 = 8,761 hours.
OpenWeather returned 8,305 rows (0 to 8304) — meaning 456 hours (~19 days) were silently omitted!

Yet df.isna().mean() * 100 printed 0.0%—because the API dropped those rows completely instead of inserting NaN!
'''










