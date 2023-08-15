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
"""Parse the intent into data used by the weather skill."""
# TODO - get rid of relative imports as soon as skills can be properly packaged with arbitrary module structures

from datetime import timedelta

from ovos_utils.time import now_local
from lingua_franca.parse import normalize

from .util import (
    get_utterance_datetime,
    get_geolocation,
    get_tz_info
)
from .weather import CURRENT
from .config import WeatherConfig


class WeatherIntent:
    _geolocation = None
    _intent_datetime = None
    _location_datetime = None

    def __init__(self, message, weather_config: WeatherConfig):
        """Constructor

        :param message: Intent data from the message bus
        :param language: The configured language of the device
        """
        self.message = message
        self.utterance = normalize(message.data["utterance"],
                                   weather_config.lang,
                                   remove_articles=False)
        self.location = message.data.get("location")
        self.config = weather_config
        self.scale = None
        self.timeframe = CURRENT

    @property
    def latitude(self):
        if self.location:
            return self.geolocation["latitude"]
        return self.config.latitude

    @property
    def longitude(self):
        if self.location:
            return self.geolocation["longitude"]
        return self.config.longitude

    @property
    def display_location(self):
        if self.geolocation:
            location = [self.geolocation["city"]]
            if self.geolocation["country"] == self.config.country:
                location.append(self.geolocation["region"])
            else:
                location.append(self.geolocation["country"])
        else:
            location = [self.config.city, self.config.country]

        return ", ".join(location)

    @property
    def geolocation(self):
        """Lookup the intent location using the geolocation API.

        The geolocation API assumes the location of a city is being
        requested.  If the user asks "What is the weather in Russia"
        the results are fuzzy

        "what is the weather in russia" can be interpreted:
        - default to capital city  <- the geolocation api would say "Россия"
        - min and max / avg across the country
        - "damn freezing" if we are sarcastic bot

        all are valid interpretations and are better than "an error occurred"
        what would you, a human, answer to the question
        """
        if self._geolocation is None:
            if self.location is None:
                self._geolocation = dict()
            else:
                self._geolocation = get_geolocation(self.location)
        return self._geolocation

    @property
    def intent_datetime(self):
        """Use the configured timezone and the utterance to know the intended time.

        If a relative date or relative time is supplied in the utterance, use a
        datetime object representing the request.  Otherwise, use the timezone
        configured by the device.
        """
        if self._intent_datetime is None:
            utterance_datetime = get_utterance_datetime(
                self.utterance,
                timezone=self.geolocation.get("timezone"),
                language=self.config.lang,
            )
            if utterance_datetime is not None:
                delta = utterance_datetime - self.location_datetime
                if int(delta / timedelta(days=1)) > 7:
                    raise ValueError("Weather forecasts only supported up to 7 days")
                if utterance_datetime.date() < self.location_datetime.date():
                    raise ValueError("Historical weather is not supported")
                self._intent_datetime = utterance_datetime
            else:
                self._intent_datetime = self.location_datetime

        return self._intent_datetime

    @property
    def location_datetime(self):
        """Determine the current date and time for the request.

        If a location is specified in the request, use the timezone for that
        location, otherwise, use the timezone configured on the device.
        """
        if self._location_datetime is None:
            if self.location is None:
                self._location_datetime = now_local()
            else:
                tz_info = get_tz_info(self.geolocation["timezone"])
                self._location_datetime = now_local(tz_info)

        return self._location_datetime
