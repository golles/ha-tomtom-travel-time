# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A custom Home Assistant integration that provides travel time sensors using the TomTom Routing and Geocoding APIs. It is distributed via HACS and installed into Home Assistant's `custom_components/` directory.

## Development Environment

The recommended environment is the devcontainer or a GitHub Codespace. For local setup:

```sh
./scripts/setup_env.sh
```

This uses [uv](https://docs.astral.sh/uv) for Python dependency management and npm for Prettier. It also installs the pre-commit hook.

## Commands

```sh
# Run tests
uv run pytest

# Run a single test file
uv run pytest tests/test_coordinator.py

# Run all linters and formatters (pre-commit)
uv run pre-commit run --all-files

# Individual linters
uv run mypy .
uv run pylint custom_components/tomtom_travel_time tests
uv run ruff check --fix
uv run ruff format .
npm run prettier -- --write .
uv run yamllint .
uv run shellcheck scripts/*.sh

# Start Home Assistant locally for manual testing
scripts/develop.sh

# Run CI checks locally (requires jq and yq)
scripts/local_ci_checks.sh
```

## Architecture

```
custom_components/tomtom_travel_time/
├── __init__.py       # Entry setup/unload; wires coordinator into config_entry.runtime_data
├── config_flow.py    # ConfigFlow + OptionsFlow; validates API key and locations on setup
├── coordinator.py    # DataUpdateCoordinator; polls TomTom Routing API every 5 minutes
├── sensor.py         # Three CoordinatorEntity sensors: duration, delay, distance
├── helpers.py        # Location resolution (lat/lon string → HA entity → geocoding fallback)
├── model.py          # TomTomTravelTimeData and UserInputLatLan dataclasses
├── diagnostics.py    # HA diagnostics support (redacts API key)
├── const.py          # Domain, config keys, default values, allowed enum values
└── translations/     # en.json and nl.json for UI strings
```

**Data flow:** `ConfigFlow` validates the API key and resolves locations (storing lat/lon strings in config entry data to avoid redundant geocoding calls on updates). On load, `__init__.py` creates a `TomTomDataUpdateCoordinator` and stores it in `config_entry.runtime_data`. The coordinator calls `RoutingApi.get_calculate_route` and returns a `TomTomTravelTimeData` dataclass. The three `TomTomSensor` entities read `duration`, `distance`, and `delay` fields from that dataclass via `getattr`.

**Location resolution** (`helpers.lat_lon_from_user_input`): tries lat/lon string pattern first, then HA's `find_coordinates` (supports entity IDs like `zone.home`), then falls back to the TomTom Geocoding API. Geocoded results are stored back as lat/lon strings in the config entry to avoid repeated geocoding.

## Testing

Tests use `pytest-homeassistant-custom-component`. The `conftest.py` auto-patches `RoutingApi` and `GeocodingApi` in all tests. The `mocked_data` fixture loads `tests/fixtures/response.json` into a `CalculatedRouteResponse` object.

Coverage is configured to track `custom_components/tomtom_travel_time` and reported to Codecov.

## Code Style

- Line length: 150 characters (ruff, pylint, prettier all configured to this)
- Ruff uses `select = ["ALL"]` with minimal ignores; Google-style docstrings
- Python 3.14 required; `from __future__ import annotations` on every module
- Imports: `custom_components.tomtom_travel_time` and `tomtom_apis` are first-party
- Test files follow `test_*.py` naming; assertions via `assert` (S101 ignored in tests)
