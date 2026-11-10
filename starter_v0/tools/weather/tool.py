from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT
from tools._team import as_int, failure, invalid_input

TOOL = "weather"
GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
SOURCE_URL = "https://open-meteo.com/"
MAX_LOCATION_CHARS = 100
CURRENT_VARS = "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m"
DAILY_VARS = "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max"

# WMO weather interpretation codes used by Open-Meteo.
WMO_VI = {
    0: "trời quang", 1: "ít mây", 2: "có mây", 3: "nhiều mây",
    45: "sương mù", 48: "sương mù đóng băng",
    51: "mưa phùn nhẹ", 53: "mưa phùn", 55: "mưa phùn dày",
    56: "mưa phùn băng giá", 57: "mưa phùn băng giá dày",
    61: "mưa nhẹ", 63: "mưa vừa", 65: "mưa to",
    66: "mưa băng giá nhẹ", 67: "mưa băng giá to",
    71: "tuyết nhẹ", 73: "tuyết vừa", 75: "tuyết dày", 77: "hạt tuyết",
    80: "mưa rào nhẹ", 81: "mưa rào", 82: "mưa rào rất to",
    85: "mưa tuyết nhẹ", 86: "mưa tuyết to",
    95: "dông", 96: "dông kèm mưa đá nhẹ", 99: "dông kèm mưa đá",
}


def describe(code: Any) -> str:
    try:
        return WMO_VI.get(int(code), f"mã thời tiết {code}")
    except (TypeError, ValueError):
        return "không rõ"


def _at(values: Any, index: int) -> Any:
    return values[index] if isinstance(values, list) and index < len(values) else None


def _place_name(place: dict[str, Any]) -> str:
    parts = [place.get("name"), place.get("admin1"), place.get("country")]
    unique: list[str] = []
    for part in parts:
        if part and part not in unique:
            unique.append(part)
    return ", ".join(unique)


def _summary(current: dict[str, Any], daily: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    if current:
        lines.append(
            f"Hiện tại {current.get('temperature_c')}°C (cảm giác {current.get('feels_like_c')}°C), "
            f"{current.get('description')}, độ ẩm {current.get('humidity_pct')}%, gió {current.get('wind_kmh')} km/h."
        )
    for day in daily:
        lines.append(
            f"{day['date']}: {day['description']}, {day['temp_min_c']}–{day['temp_max_c']}°C, "
            f"khả năng mưa {day['precipitation_probability_pct']}%."
        )
    return " ".join(lines)


def get_weather(location: str = "", days: Any = 1) -> dict[str, Any]:
    location = " ".join(str(location or "").split())
    if not location:
        return invalid_input(TOOL, "location is required (city name, e.g. 'Hà Nội')")
    if len(location) > MAX_LOCATION_CHARS:
        return invalid_input(TOOL, f"location must be at most {MAX_LOCATION_CHARS} characters")
    days = as_int(days, default=1, low=1, high=7)

    try:
        geo = requests.get(
            GEOCODE_URL,
            params={"name": location, "count": 1, "language": "vi", "format": "json"},
            timeout=TIMEOUT,
        )
        geo.raise_for_status()
        results = geo.json().get("results") or []
        if not results:
            return {
                "tool": TOOL,
                "ok": False,
                "error": "location_not_found",
                "message": f"No place named '{location}'. Ask the user for a nearby city name.",
            }
        place = results[0]

        forecast = requests.get(
            FORECAST_URL,
            params={
                "latitude": place["latitude"],
                "longitude": place["longitude"],
                "current": CURRENT_VARS,
                "daily": DAILY_VARS,
                "timezone": "auto",
                "forecast_days": days,
            },
            timeout=TIMEOUT,
        )
        forecast.raise_for_status()
        data = forecast.json()

        raw_current = data.get("current") or {}
        current = {
            "time": raw_current.get("time"),
            "temperature_c": raw_current.get("temperature_2m"),
            "feels_like_c": raw_current.get("apparent_temperature"),
            "humidity_pct": raw_current.get("relative_humidity_2m"),
            "precipitation_mm": raw_current.get("precipitation"),
            "wind_kmh": raw_current.get("wind_speed_10m"),
            "description": describe(raw_current.get("weather_code")),
        } if raw_current else {}

        raw_daily = data.get("daily") or {}
        daily = [{
            "date": date,
            "description": describe(_at(raw_daily.get("weather_code"), index)),
            "temp_min_c": _at(raw_daily.get("temperature_2m_min"), index),
            "temp_max_c": _at(raw_daily.get("temperature_2m_max"), index),
            "precipitation_probability_pct": _at(raw_daily.get("precipitation_probability_max"), index),
        } for index, date in enumerate(raw_daily.get("time") or [])]

        name = _place_name(place)
        return {
            "tool": TOOL,
            "ok": True,
            "location": {
                "name": name,
                "latitude": place.get("latitude"),
                "longitude": place.get("longitude"),
                "timezone": data.get("timezone") or place.get("timezone"),
            },
            "current": current,
            "daily": daily,
            "items": [{"title": f"Thời tiết {name}", "url": SOURCE_URL, "source": "open-meteo.com", "summary": _summary(current, daily)}],
        }
    except Exception as exc:
        return failure(TOOL, exc)
