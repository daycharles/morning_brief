"""Weather fetcher — retrieves Open-Meteo LA daily forecast (High/Low °F and precipitation)."""
import logging

from scripts.utils.fetch_result import FetchResult
from scripts.utils.http_client import get

logger = logging.getLogger(__name__)

_API_URL = "https://api.open-meteo.com/v1/forecast"
_LATITUDE = 34.0522   # Los Angeles, CA
_LONGITUDE = -118.2437


def _celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit, rounded to 1 decimal place."""
    return round((celsius * 9 / 5) + 32, 1)


def fetch(config: dict) -> FetchResult:
    """Fetch today's LA weather forecast from Open-Meteo.

    Args:
        config: Unused for Open-Meteo (no authentication required).

    Returns:
        FetchResult with status='success' and data={'high_f', 'low_f', 'precipitation_probability'}
        on success. FetchResult with status='failed' on any error.
    """
    try:
        params = {
            "latitude": _LATITUDE,
            "longitude": _LONGITUDE,
            "daily": ["temperature_2m_max", "temperature_2m_min", "precipitation_probability_max"],
            "timezone": "America/Los_Angeles",
            "forecast_days": 1,
        }

        response = get(_API_URL, params=params)

        daily = response.get("daily", {})
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_probability_max", [])

        if not max_temps or not min_temps:
            logger.warning("Weather: empty or missing daily temperature data")
            return FetchResult(
                source="weather",
                status="success",
                data={"message": "Weather data unavailable."},
            )

        high_f = _celsius_to_fahrenheit(max_temps[0])
        low_f = _celsius_to_fahrenheit(min_temps[0])
        precipitation_probability = int(precip[0]) if precip else 0

        data = {
            "high_f": high_f,
            "low_f": low_f,
            "precipitation_probability": precipitation_probability,
        }

        logger.info(
            "Weather: LA forecast High=%.1f°F Low=%.1f°F Precip=%d%%",
            high_f, low_f, precipitation_probability,
        )

        return FetchResult(source="weather", status="success", data=data)

    except Exception as exc:
        logger.warning("Weather fetch failed: %s", exc)
        return FetchResult(source="weather", status="failed", error_message=str(exc))
