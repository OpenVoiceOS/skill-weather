# Copyright 2021, Mycroft AI Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Utility functions for the weather skill."""
from datetime import datetime, timedelta, tzinfo
from itertools import islice
from typing import List

import pytz
import requests
from ovos_config import Configuration
from ovos_date_parser import nice_date, extract_datetime
from ovos_utils import timed_lru_cache
from ovos_utils.time import now_local, to_local

try:
    from timezonefinder import TimezoneFinder
except ImportError:
    TimezoneFinder = None


# Geolocation Api
@timed_lru_cache(seconds=600)  # cache results for 10 mins
def _get_geolocation(location):
    """Call the geolocation endpoint.

    Args:
        location (str): the location to lookup (e.g. Kansas City Missouri)

    Returns:
        str: JSON structure with lookup results
    """
    url = "https://nominatim.openstreetmap.org/search"

    data = requests.get(url, params={"q": location, "format": "json", "limit": 1},
                        headers={"User-Agent": "OVOS/1.0"}).json()[0]
    lat = data.get("lat")
    lon = data.get("lon")

    if lat and lon:
        return get_reverse_geolocation(lat, lon)

    url = "https://nominatim.openstreetmap.org/details.php"
    details = requests.get(url, params={"osmid": data['osm_id'], "osmtype": data['osm_type'][0].upper(),
                                        "format": "json"},
                           headers={"User-Agent": "OVOS/1.0"}).json()

    # if no addresstags are present for the location an empty list is sent instead of a dict
    tags = details.get("addresstags") or {}

    place_type = details["extratags"].get("linked_place") or details.get("category") or data.get(
        "type") or data.get("class")
    name = details["localname"] or details["names"].get("name") or details["names"].get("official_name") or data[
        "display_name"]
    cc = details["country_code"] or tags.get("country") or details["extratags"].get('ISO3166-1:alpha2') or ""
    # TODO - lang support, official name is reported in various langs
    location = {
        "address": data["display_name"],
        "city": {
            "code": tags.get("postcode") or
                    details["calculated_postcode"] or "",
            "name": name if place_type == "city" else "",
            "state": {
                "code": tags.get("state_code") or
                        details["calculated_postcode"] or "",
                "name": name if place_type == "state" else tags.get("state"),
                "country": {
                    "code": cc.upper(),
                    "name": name if place_type == "country" else ""  # TODO - country code to name
                }
            }
        },
        "coordinate": {
            "latitude": lat,
            "longitude": lon
        }
    }
    if "timezone" not in location:
        location["timezone"] = _get_timezone(lon=lon, lat=lat)
    return location


@timed_lru_cache(seconds=600)  # cache results for 10 mins
def get_reverse_geolocation(lat, lon):
    """Call the reverse geolocation endpoint.

    Args:
        lat (float): latitude
        lon (float): longitude

    Returns:
        str: JSON structure with lookup results
    """
    url = "https://nominatim.openstreetmap.org/reverse"
    details = requests.get(url, params={"lat": lat, "lon": lon, "format": "json"},
                           headers={"User-Agent": "OVOS/1.0"}).json()
    address = details.get("address")
    location = {
        "address": details["display_name"],
        "city": {
            "code": address.get("postcode") or "",
            "name": address.get("city") or
                    address.get("village") or
                    address.get("town") or
                    address.get("hamlet") or
                    address.get("county") or "",
            "state": {
                "code": address.get("state_code") or
                        address.get("ISO3166-2-lvl4") or
                        address.get("ISO3166-2-lvl6")
                        or "",
                "name": address.get("state") or
                        address.get("county")
                        or "",
                "country": {
                    "code": address.get("country_code", "").upper() or "",
                    "name": address.get("country") or "",
                }
            }
        },
        "coordinate": {
            "latitude": details.get("lat") or lat,
            "longitude": details.get("lon") or lon
        }
    }
    if "timezone" not in location:
        location["timezone"] = _get_timezone(
            lat=details.get("lat") or lat,
            lon=details.get("lon") or lon)
    return location


def _get_lat_lon(**kwargs):
    lat = kwargs.get("latitude") or kwargs.get("lat")
    lon = kwargs.get("longitude") or kwargs.get("lon") or kwargs.get("lng")
    if not lat or not lon:
        cfg = Configuration().get("location", {}).get("coordinate", {})
        lat = cfg.get("latitude")
        lon = cfg.get("longitude")
    return lat, lon


def _get_timezone(**kwargs):
    if TimezoneFinder:
        lat, lon = _get_lat_lon(**kwargs)
        tz = TimezoneFinder().timezone_at(lng=float(lon), lat=float(lat))
        return {
            "name": tz.replace("/", " "),
            "code": tz
        }
    else:
        cfg = Configuration().get("location", {}).get("timezone")
        return cfg or {"name": "UTC", "code": "UTC"}


class LocationNotFoundError(ValueError):
    """Raise when the API cannot find the requested location."""
    pass


def convert_to_local_datetime(isodate: str, timezone: str) -> datetime:
    """Convert a timestamp to a datetime object in the requested timezone.

    This function assumes it is passed a timestamp in the UTC timezone.  It
    then adjusts the datetime to match the specified timezone.

    Args:
        isodate: seconds since epoch
        timezone: the timezone of the weather report

    Returns:
        A datetime in the user timezone
    """
    naive_datetime = datetime.fromisoformat(isodate)
    tz_datetime = naive_datetime.astimezone(pytz.timezone(timezone))
    return to_local(tz_datetime)


def get_utterance_datetime(
        utterance: str, timezone: str = None, language: str = None
) -> datetime:
    """Get a datetime representation of a date or time concept in an utterance.

    Args:
        utterance: the words spoken by the user
        timezone: the timezone requested by the user
        language: the language configured on the device

    Returns:
        The date and time represented in the utterance in the specified timezone.
    """
    utterance_datetime = None
    if timezone is None:
        anchor_date = None
    else:
        intent_timezone = get_tz_info(timezone)
        anchor_date = datetime.now(intent_timezone)
    extract = extract_datetime(utterance, anchorDate=anchor_date, lang=language)
    if extract is not None:
        utterance_datetime, _ = extract
    return utterance_datetime


def get_tz_info(timezone: str) -> tzinfo:
    """Generate a tzinfo object from a timezone string.

    Args:
        timezone: a string representing a timezone

    Returns:
        timezone in a string format
    """
    return pytz.timezone(timezone)


def get_geolocation(location: str):
    """Retrieve the geolocation information about the requested location.

    Args:
        location: a location specified in the utterance

    Returns:
        A deserialized JSON object containing geolocation information for the
        specified city.

    Raises:
        LocationNotFound error if the API returns no results.
    """
    geolocation = _get_geolocation(location)

    if geolocation is None:
        raise LocationNotFoundError(f"Location {location} is unknown")

    # convert the dict to a simpler format
    return {
        "city": geolocation["city"]["name"],
        "region": geolocation["city"]["state"]["name"],
        "country": geolocation["city"]["state"]["country"]["name"],
        "latitude": geolocation["coordinate"]["latitude"],
        "longitude": geolocation["coordinate"]["longitude"],
        "timezone": geolocation["timezone"]["code"]
    }


def get_time_period(intent_datetime: datetime) -> str:
    """Translate a specific time '9am' to period of the day 'morning'

    Args:
        intent_datetime: the datetime extracted from an utterance

    Returns:
        A generalized time of day based on the passed datetime object.
    """
    hour = intent_datetime.time().hour
    if 1 <= hour < 5:
        period = "early morning"
    elif 5 <= hour < 12:
        period = "morning"
    elif 12 <= hour < 17:
        period = "afternoon"
    elif 17 <= hour < 20:
        period = "evening"
    else:
        period = "overnight"
    return period


def get_speakable_day_of_week(date_to_speak: datetime, lang: str):
    """Convert the time of the a daily weather forecast to a speakable day of week.

    Args:
        date_to_speak: The date/time for the forecast being reported.

    Returns:
        The day of the week in the device's configured language
    """
    now = now_local()
    tomorrow = now.date() + timedelta(days=1)

    # A little hack to prevent nice_date() from returning "tomorrow"
    if date_to_speak.date() == tomorrow:
        now_arg = now - timedelta(days=1)
    else:
        now_arg = now

    speakable_date = nice_date(date_to_speak, now=now_arg, lang=lang)
    day_of_week = speakable_date.split(",")[0]

    return day_of_week


def chunk_list(it: list, size: int) -> List[tuple]:
    """Takes in a list and chops it in `size` length tuples

    Args:
        it (list): list to chop
        size (int): size of the chunks

    Returns:
        List[tuple]: a list of tuple containing the chunks
    """
    it = iter(it)
    return list(iter(lambda: tuple(islice(it, size)), ()))
