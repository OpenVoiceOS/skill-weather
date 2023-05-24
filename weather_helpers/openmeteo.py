import requests
from ovos_utils import timed_lru_cache

# TODO - get rid of relative imports
# /home/miro/PycharmProjects/.venvs/ovos/bin/python /home/miro/PycharmProjects/skill-ovos-weather/weather_helpers/openmeteo.py
# Traceback (most recent call last):
#   File "/home/miro/PycharmProjects/skill-ovos-weather/weather_helpers/openmeteo.py", line 3, in <module>
#     from .config import *
# ImportError: attempted relative import with no known parent package
# so annoying
from datetime import datetime as dt

from .util import chunk_list
from .config import *
from .weather import WeatherReport

def sliced(data: dict) -> dict:
    """
    Openmeteo is sending data starting at 00:00 local-time,
    This slices the hourly data up until the current hour.

    Args:
        data (dict): the weather json report sent from om

    Returns:
        dict: the sliced report
    """
    time = data.get("current_weather",{}).get("time")
    hour = dt.fromisoformat(time).hour

    for k, v in data["hourly"].items():
        # compute missing/nice to have daily parameters
        if k == "relativehumidity_2m":
            data["daily"][k] = [int(sum(tup)/len(tup)) for tup
                                in chunk_list(v, 24)]
        # slice data
        if isinstance(v, list):
            data["hourly"][k] = v[hour:]

    return data


@timed_lru_cache(seconds=60 * 15)  # cache for 15 mins
def get_report(cfg: WeatherConfig):
    if cfg.speed_unit == MILES_PER_HOUR:
        windspeed_unit = "mph"
    elif cfg.speed_unit == METER_PER_SECOND:
        windspeed_unit = "ms"
    elif cfg.speed_unit == KILOMETER_PER_HOUR:
        windspeed_unit = "kmh"
    else:
        raise ValueError("invalid speed unit")

    if cfg.temperature_unit == CELSIUS:
        temperature_unit = "celsius"
    elif cfg.temperature_unit == FAHRENHEIT:
        temperature_unit = "fahrenheit"
    else:
        raise ValueError("invalid temperature unit")

    if cfg.precipitation_unit == MILLIMETER:
        precipitation_unit = "mm"
    elif cfg.precipitation_unit == INCH:
        precipitation_unit = "inch"
    else:
        raise ValueError("invalid precipitation unit")

    daily_params = [
        "temperature_2m_max",
        "temperature_2m_min",
        "apparent_temperature_max",
        "apparent_temperature_min",
        "precipitation_sum",
        "precipitation_hours",
        "weathercode",
        "sunrise",
        "sunset",
        "windspeed_10m_max",
        "windgusts_10m_max",
        "winddirection_10m_dominant",
        "shortwave_radiation_sum",
        "et0_fao_evapotranspiration",
        "uv_index_max",
        "precipitation_probability_mean",
        "precipitation_probability_min",
        "precipitation_probability_max",
        "uv_index_clear_sky_max"]
    hourly_params = ["temperature_2m",
                     "relativehumidity_2m",
                     "dewpoint_2m",
                     "apparent_temperature",
                     "pressure_msl",
                     "surface_pressure",
                     "cloudcover",
                     "cloudcover_low",
                     "cloudcover_mid",
                     "cloudcover_high",
                     "windspeed_10m",
                     "windspeed_80m",
                     "windspeed_120m",
                     "windspeed_180m",
                     "winddirection_10m",
                     "winddirection_80m",
                     "winddirection_120m",
                     "winddirection_180m",
                     "windgusts_10m",
                     "shortwave_radiation",
                     "direct_radiation",
                     "diffuse_radiation",
                     "vapor_pressure_deficit",
                     "cape",
                     "evapotranspiration",
                     "et0_fao_evapotranspiration",
                     "precipitation",
                     "weathercode",
                     "snow_depth",
                     "showers",
                     "snowfall",
                     "visibility",
                     "precipitation_probability",
                     "freezinglevel_height",
                     "soil_temperature_0cm",
                     "soil_temperature_6cm",
                     "soil_temperature_18cm",
                     "soil_temperature_54cm",
                     "soil_moisture_0_1cm",
                     "soil_moisture_1_3cm",
                     "soil_moisture_3_9cm",
                     "soil_moisture_9_27cm",
                     "soil_moisture_27_81cm",
                     "relativehumidity_1000hPa",
                     "is_day"]

    args = {
        "longitude": cfg.longitude,
        "latitude": cfg.latitude,
        "hourly": ','.join(hourly_params),
        "daily": ','.join(daily_params),
        "current_weather": True,
        "temperature_unit": temperature_unit,  # fahrenheit
        "windspeed_unit": windspeed_unit,  # ms, mph, kn
        "precipitation_unit": precipitation_unit,  # inch
        "timezone": cfg.timezone  # gmt ...
    }
    url = f"https://api.open-meteo.com/v1/forecast"
    data = sliced(requests.get(url, params=args).json())
    return WeatherReport(data)
