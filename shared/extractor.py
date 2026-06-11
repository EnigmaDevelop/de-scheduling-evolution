# shared/extractor.py

import logging
from typing import Any

import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from shared.models import RawWeatherResponse, WeatherRecord

# ---------------------------------------------------------------------------
# Logger setup
# ---------------------------------------------------------------------------

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
DEFAULT_UNITS = "metric"        # Celsius
DEFAULT_TIMEOUT = 10            # seconds


# ---------------------------------------------------------------------------
# Retry-decorated HTTP call
# Retries on network errors and 5xx responses
# Exponential backoff: 2s → 4s → 8s (max 3 attempts)
# ---------------------------------------------------------------------------

@retry(
    retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _fetch_raw(api_key: str, city: str, units: str = DEFAULT_UNITS) -> dict[str, Any]:
    """
    Low-level HTTP GET to OpenWeatherMap API.
    Returns raw JSON dict.
    Raises on non-200 responses after retries.
    """
    params = {
        "q": city,
        "appid": api_key,
        "units": units,
    }

    response = requests.get(BASE_URL, params=params, timeout=DEFAULT_TIMEOUT)

    # Raise immediately on 4xx (bad api key, city not found etc.)
    # Do not retry on client errors
    if response.status_code == 401:
        raise ValueError(f"Invalid API key")
    if response.status_code == 404:
        raise ValueError(f"City not found: {city}")

    # Raise on any other non-200
    response.raise_for_status()

    return response.json()


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def extract(api_key: str, city: str, units: str = DEFAULT_UNITS) -> WeatherRecord:
    """
    Main entry point for extraction layer.
    Fetches → validates → transforms → returns WeatherRecord.

    Args:
        api_key : OpenWeatherMap API key
        city    : City name e.g. "Istanbul"
        units   : "metric" | "imperial" | "standard"

    Returns:
        WeatherRecord ready to be passed to loader

    Raises:
        ValueError      : Invalid API key or city not found
        requests.Error  : Network errors after retries exhausted
        ValidationError : Unexpected API response shape
    """
    logger.info(f"Extracting weather data | city={city} units={units}")

    # Step 1: HTTP call with retry
    raw_dict = _fetch_raw(api_key=api_key, city=city, units=units)

    # Step 2: Validate and parse raw response
    raw_response = RawWeatherResponse.model_validate(raw_dict)

    # Step 3: Transform to clean model
    record = WeatherRecord.from_raw(raw_response)

    logger.info(
        f"Extraction successful | city={record.city} "
        f"temp={record.temp}°C ts={record.timestamp}"
    )

    return record
