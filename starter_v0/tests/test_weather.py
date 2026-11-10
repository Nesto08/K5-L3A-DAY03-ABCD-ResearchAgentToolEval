"""Unit tests for the `weather` tool (Open-Meteo geocoding + forecast), fully mocked."""
from __future__ import annotations

from typing import Any

import pytest
import requests

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

weather_tool = TOOL_FUNCTIONS["weather"]

GEOCODE = {"results": [{
    "name": "Hà Nội", "latitude": 21.0245, "longitude": 105.84117,
    "country": "Việt Nam", "admin1": "Hanoi", "timezone": "Asia/Bangkok",
}]}
FORECAST = {
    "timezone": "Asia/Bangkok",
    "current": {
        "time": "2026-11-10T12:30", "temperature_2m": 19.5, "relative_humidity_2m": 57,
        "apparent_temperature": 18.0, "precipitation": 0.0, "weather_code": 3, "wind_speed_10m": 11.2,
    },
    "daily": {
        "time": ["2026-11-10", "2026-11-11"], "weather_code": [51, 3],
        "temperature_2m_max": [19.8, 23.2], "temperature_2m_min": [15.6, 15.9],
        "precipitation_probability_max": [71, 8],
    },
}


@pytest.fixture
def open_meteo(monkeypatch):
    """Route requests.get by URL: geocoding and forecast get different fake responses."""

    def _install(geocode: Any = GEOCODE, forecast: Any = FORECAST) -> list[dict[str, Any]]:
        calls: list[dict[str, Any]] = []

        def _get(url: str, **kwargs: Any) -> FakeResponse:
            calls.append({"url": url, **kwargs})
            response = geocode if "geocoding" in url else forecast
            if isinstance(response, Exception):
                raise response
            return response if isinstance(response, FakeResponse) else FakeResponse(response)

        monkeypatch.setattr(requests, "get", _get)
        return calls

    return _install


def test_weather_geocodes_then_requests_forecast_for_those_coordinates(open_meteo) -> None:
    calls = open_meteo()

    result = weather_tool(location="  Hà   Nội ", days=2)

    assert len(calls) == 2
    assert "geocoding-api.open-meteo.com" in calls[0]["url"]
    assert calls[0]["params"]["name"] == "Hà Nội"
    assert "api.open-meteo.com/v1/forecast" in calls[1]["url"]
    assert calls[1]["params"]["latitude"] == 21.0245
    assert calls[1]["params"]["longitude"] == 105.84117
    assert calls[1]["params"]["forecast_days"] == 2
    assert all(call["timeout"] for call in calls)


def test_weather_maps_current_daily_and_items(open_meteo) -> None:
    open_meteo()

    result = weather_tool(location="Hà Nội", days=2)

    assert result["ok"] is True
    assert result["location"]["name"] == "Hà Nội, Hanoi, Việt Nam"
    assert result["current"]["temperature_c"] == 19.5
    assert result["current"]["description"] == "nhiều mây"
    assert result["daily"][0] == {
        "date": "2026-11-10", "description": "mưa phùn nhẹ",
        "temp_min_c": 15.6, "temp_max_c": 19.8, "precipitation_probability_pct": 71,
    }
    item = result["items"][0]
    assert item["source"] == "open-meteo.com"
    assert "19.5°C" in item["summary"] and "71%" in item["summary"]


@pytest.mark.parametrize("location", ["", "   ", None, "x" * 101])
def test_weather_bad_location_from_model_does_not_call_network(open_meteo, location) -> None:
    calls = open_meteo()

    result = weather_tool(location=location)

    assert result["ok"] is False
    assert result["error"] == "invalid_input"
    assert calls == []


@pytest.mark.parametrize("days, expected", [("3", 3), (0, 1), (30, 7), ("abc", 1), (None, 1), (2.9, 2)])
def test_weather_days_is_coerced_and_clamped(open_meteo, days, expected) -> None:
    calls = open_meteo()

    weather_tool(location="Huế", days=days)

    assert calls[1]["params"]["forecast_days"] == expected


def test_weather_unknown_place_returns_location_not_found_without_forecast_call(open_meteo) -> None:
    calls = open_meteo(geocode={"generationtime_ms": 0.1})

    result = weather_tool(location="Atlantis")

    assert result["ok"] is False
    assert result["error"] == "location_not_found"
    assert len(calls) == 1


def test_weather_http_error_returns_error_dict(open_meteo) -> None:
    open_meteo(forecast=FakeResponse(status_code=500))

    result = weather_tool(location="Hà Nội")

    assert result["ok"] is False
    assert result["error"] == "HTTPError"


def test_weather_network_timeout_returns_error_dict(open_meteo) -> None:
    open_meteo(geocode=requests.Timeout("timed out"))

    result = weather_tool(location="Hà Nội")

    assert result["ok"] is False
    assert result["error"] == "Timeout"


def test_weather_unknown_wmo_code_does_not_crash(open_meteo) -> None:
    forecast = {**FORECAST, "current": {**FORECAST["current"], "weather_code": 42}}
    open_meteo(forecast=forecast)

    result = weather_tool(location="Hà Nội")

    assert result["current"]["description"] == "mã thời tiết 42"
