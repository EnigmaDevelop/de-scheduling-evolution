# shared/models.py

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Raw API Response Models
# Directly maps to OpenWeatherMap Current Weather JSON response
# ---------------------------------------------------------------------------


class WeatherCondition(BaseModel):
    """Maps to weather[0] in API response"""
    id: int
    main: str           # e.g. "Clear", "Rain", "Clouds"
    description: str    # e.g. "clear sky", "light rain"
    icon: str           # e.g. "01d", "10n"


class MainMetrics(BaseModel):
    """Maps to main{} block in API response"""
    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: int
    humidity: int


class Wind(BaseModel):
    """Maps to wind{} block in API response"""
    speed: float
    deg: int


class Clouds(BaseModel):
    """Maps to clouds{} block in API response"""
    all: int            # cloudiness percentage


class RawWeatherResponse(BaseModel):
    """
    Full API response model.
    Captures raw JSON before any transformation.
    """
    weather: list[WeatherCondition]
    main: MainMetrics
    wind: Wind
    clouds: Clouds
    dt: int             # Unix timestamp from API
    name: str           # City name
    cod: int            # HTTP-like status code from API
    raw: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def capture_raw(cls, values: Any) -> Any:
        """
        Runs before field validation.
        Stores the original dict as raw before Pydantic touches it.
        """
        if isinstance(values, dict):
            values["raw"] = dict(values)
        return values


# ---------------------------------------------------------------------------
# Clean / Parsed Model
# This is what gets written to PostgreSQL
# ---------------------------------------------------------------------------


class WeatherRecord(BaseModel):
    """
    Transformed, clean model.
    One row in the weather_records table.
    """
    city: str
    timestamp: datetime         # UTC, timezone-aware
    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: int
    humidity: int
    wind_speed: float
    wind_deg: int
    weather_main: str           # e.g. "Clear"
    weather_desc: str           # e.g. "clear sky"
    raw: dict[str, Any]         # original API response, buffer layer

    @classmethod
    def from_raw(cls, raw: RawWeatherResponse) -> "WeatherRecord":
        """
        Factory method. Single place for transformation logic.
        RawWeatherResponse → WeatherRecord
        """
        return cls(
            city=raw.name,
            timestamp=datetime.fromtimestamp(raw.dt, tz=timezone.utc),
            temp=raw.main.temp,
            feels_like=raw.main.feels_like,
            temp_min=raw.main.temp_min,
            temp_max=raw.main.temp_max,
            pressure=raw.main.pressure,
            humidity=raw.main.humidity,
            wind_speed=raw.wind.speed,
            wind_deg=raw.wind.deg,
            weather_main=raw.weather[0].main,
            weather_desc=raw.weather[0].description,
            raw=raw.raw,
        )
