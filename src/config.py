import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# "KARACHI"
LATITUDE = 24.8608
LONGITUDE = 67.0104

OPENMETEO_AIR_QUALITY_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

OPENMETEO_HISTORICAL_URL = "https://archive-api.open-meteo.com/v1/archive"

OPENMETEO_RECENT_DATA_URL = "https://api.open-meteo.com/v1/forecast"

OPENWEATHER_URL= "https://api.openweathermap.org/data/2.5/air_pollution/history"

OPEN_WEATHER_API_KEY = os.getenv("OPEN_WEATHER_API_KEY")

HOPSWORKS_API_KEY = os.getenv("HOPSWORKS_API_KEY")

HOPSWORKS_PROJECT = os.getenv("HOPSWORKS_PROJECT")

FEATURE_GROUP_NAME = "karachi_weather_features"

FEATURE_GROUP_VERSION = 1

REQUEST_TIMEOUT = 15


