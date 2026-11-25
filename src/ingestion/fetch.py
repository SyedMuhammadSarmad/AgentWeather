import requests
import pandas as pd 
from src.config import LATITUDE, LONGITUDE, OPENMETEO_AIR_QUALITY_URL, REQUEST_TIMEOUT

def fetch_om_air_quality(start:str, end:str) -> pd.DataFrame:
    params = {
	    "latitude": LATITUDE,
	    "longitude": LONGITUDE,
	    "hourly": ["pm10", "pm2_5", "uv_index", "us_aqi"],
        "start_date": start,
	    "end_date": end,
        "timezone":"UTC",
    } 
    
    response = requests.get(OPENMETEO_AIR_QUALITY_URL,params,timeout = REQUEST_TIMEOUT)
    response.raise_for_status()
    json_response = response.json()

    df = pd.DataFrame(json_response["hourly"])
    
    df['time'] = pd.to_datetime(df['time'],utc=True)

    df = df.loc[ df['time'] <= pd.Timestamp.now(tz = "UTC").floor("h")]
  
    df = df.rename(columns = {"pm2_5":"om_pm2_5","pm10":"om_pm10"})

    df = df.drop_duplicates(subset=["time"],keep='first').sort_values("time").reset_index(drop = True)

    return df


if __name__ == "__main__":
    df = fetch_om_air_quality("2026-11-15", "2026-11-22")
    print(df.shape)
    print(df.head(3))
    print(df.tail(3))

