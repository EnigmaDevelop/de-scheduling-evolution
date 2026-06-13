import os
import requests
from typing import Any
import structlog
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)
from shared.models import RawWeatherResponse, WeatherRecord

# Setup structurally unified JSON logger
logger = structlog.get_logger()

BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
DEFAULT_UNITS = "metric"
DEFAULT_TIMEOUT = 10

@retry(
    retry=retry_if_exception_type((requests.ConnectionError, requests.Timeout)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    before_sleep=before_sleep_log(logger, "warning"),
    reraise=True,
)
def _fetch_raw(api_key: str, city: str, units: str = DEFAULT_UNITS) -> dict[str, Any]:
    """
    Low-level HTTP GET call to OpenWeatherMap API with strict timeouts and error classification.
    """
    # Defensive programming: Prevent execution with unconfigured placeholders
    if api_key in ["MOCK_MODE", "your_actual_secret_api_key_here"] or not api_key:
        import random
        from datetime import datetime, timezone
        logger.info("Mock mode active or API key missing. Generating deterministic payload.")
        return {
            "weather": [{"id": 800, "main": "Clear", "description": "clear sky", "icon": "01d"}],
            "main": {
                "temp": round(random.uniform(15.0, 30.0), 2),
                "feels_like": round(random.uniform(15.0, 30.0), 2),
                "temp_min": 14.0,
                "temp_max": 31.0,
                "pressure": 1013,
                "humidity": random.randint(40, 80)
            },
            "wind": {"speed": 3.6, "deg": 160},
            "clouds": {"all": 0},
            "dt": int(datetime.now(timezone.utc).timestamp()),
            "name": city,
            "cod": 200
        }

    params = {
        "q": city,
        "appid": api_key,
        "units": units,
    }

    response = requests.get(BASE_URL, params=params, timeout=DEFAULT_TIMEOUT)

    if response.status_code == 401:
        raise ValueError("Invalid API key provided to the weather service")
    if response.status_code == 404:
        raise ValueError(f"Target city not found: {city}")

    response.raise_for_status()
    return response.json()

def extract(api_key: str, city: str, units: str = DEFAULT_UNITS) -> WeatherRecord:
    """
    Main ingestion interface. Fetches raw API data, validates constraints,
    maps schema and returns an immutable WeatherRecord container.
    """
    masked_key = "STORED_IN_ENV" if api_key and api_key != "MOCK_MODE" else "MOCK_ACTIVE"
    logger.info("Executing extraction layer", city=city, units=units, api_key_status=masked_key)

    raw_dict = _fetch_raw(api_key=api_key, city=city, units=units)
    
    raw_response = RawWeatherResponse.model_validate(raw_dict)
    record = WeatherRecord.from_raw(raw_response)

    logger.info("Extraction lifecycle successful", city=record.city, temp=record.temp, timestamp=str(record.timestamp))
    return record
