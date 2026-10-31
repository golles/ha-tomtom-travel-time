# TomTom Travel Time

[![GitHub Release][releases-shield]][releases]
[![GitHub Repo stars][stars-shield]][stars]
[![License][license-shield]](LICENSE)
[![GitHub Activity][commits-shield]][commits]
[![Code coverage][codecov-shield]][codecov]
[![hacs][hacs-shield]][hacs]
[![installs][hacs-installs-shield]][ha-active-installation-badges]
[![Project Maintenance][maintenance-shield]][maintainer]
[![BuyMeCoffee][buymecoffeebadge]][buymecoffee]

The TomTom Travel Time integration provides travel time information using TomTom services.

## Installation

### Method 1: HACS (Recommended)

1. Open HACS in your Home Assistant instance.
2. Go to "Integrations".
3. Click the "+" button.
4. Search for "TomTom Travel Time".
5. Click "Download" and restart Home Assistant.

### Method 2: Manual Installation

1. Download the latest release from [GitHub releases](https://github.com/golles/ha-tomtom-travel-time/releases).
2. Extract the files to your Home Assistant `custom_components` directory:
   ```
   config/
   └── custom_components/
     └── tomtom_travel_time/
       ├── __init__.py
       ├── manifest.json
       └── ... (all other files)
   ```
3. Restart Home Assistant.

## API key

To use the TomTom Travel Time integration, you need a (free) TomTom API key. You can obtain one by signing up at the [TomTom Developer Portal](https://developer.tomtom.com/).

1. Go to **API & SDK Keys** and click **Create Key**.
2. Enter a name, e.g., **"Home Assistant Integration"**.
3. Under "Products", select **Routing API** and **Geocoding API**
4. Click **Create Key**.
5. Click on your new API key to copy it.

## Configuration

Configuration is done entirely through the Home Assistant UI—no YAML editing required!

### Quick Start

1. Go to **Settings** → **Devices & Services**.
2. Click **"+ Add Integration"**.
3. Search for **"TomTom Travel Time"**.
4. Follow the setup wizard to create the sensors.

![Add integration](/img/add.png)

![Sensors](/img/sensors.png)

![Set options](/img/options.png)

### Update interval and API quota

Every update of a route uses one TomTom Routing API request. The update interval can be changed per route in the options (default: 5 minutes).

The free TomTom plan has a monthly quota (check the current limits for your key in the [TomTom Developer Portal](https://developer.tomtom.com/)). With a free quota of 20,000 Routing API requests per month, this is roughly what fits:

| Routes | Minimum update interval |
| ------ | ----------------------- |
| 1      | 3 minutes               |
| 2      | 5 minutes               |
| 3      | 7 minutes               |
| 4      | 9 minutes               |

Formula: `routes × 60 × 24 × 31 / interval in minutes ≤ monthly quota`.

When the quota is exceeded, TomTom responds with `HTTP 403 Forbidden` and the sensors become unavailable until the quota resets.

#### Only update when you need it

If you only need travel times at certain moments (e.g. before your commute), you can disable polling and update the sensors with an automation instead:

1. Go to **Settings** → **Devices & Services** → **TomTom Travel Time**.
2. Click the three dots menu of the route and select **System options**.
3. Disable **Enable polling for updates**.
4. Create an automation that calls the `homeassistant.update_entity` action, for example:

```yaml
automation:
  - alias: Update travel time during commute
    triggers:
      - trigger: time_pattern
        minutes: /5
    conditions:
      - condition: time
        after: "07:00:00"
        before: "09:00:00"
        weekday: [mon, tue, wed, thu, fri]
    actions:
      - action: homeassistant.update_entity
        target:
          entity_id: sensor.home_work_duration
```

## Troubleshooting

### Debug Logging

To collect detailed logs for troubleshooting:

#### Method 1: Integration Debug (Recommended)

1. Go to **Settings** → **Devices & Services** → **TomTom Travel Time**.
2. Click the three dots menu in the top right corner.
3. Click **"Enable debug logging"**.
4. Reproduce the issue.
5. Click **"Stop debug logging"** to download the log file.

#### Method 2: Logger Configuration

Add this to your `configuration.yaml`:

```yaml
logger:
  default: warn
  logs:
    custom_components.tomtom_travel_time: debug
    tomtom_apis: debug
```

For more information, see the [Home Assistant Logger Integration](https://www.home-assistant.io/integrations/logger).

### Getting Help

1. Check the [existing issues](https://github.com/golles/ha-tomtom-travel-time/issues) first.
2. If you find a new issue, [create a detailed bug report](https://github.com/golles/ha-tomtom-travel-time/issues/new).
3. Include debug logs and the integration diagnostics file.

## Contributing

Contributions are welcome! This project is open source and benefits from community involvement.

### How to Contribute

1. **Report Issues**: Found a bug or have a feature request? [Open an issue](https://github.com/golles/ha-tomtom-travel-time/issues).
2. **Code Contributions**: Check the [Contribution Guidelines](CONTRIBUTING.md) for development setup.
3. **Device Support**: Help expand device compatibility by testing with your hardware.

### Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development setup instructions.

[buymecoffee]: https://www.buymeacoffee.com/golles
[buymecoffeebadge]: https://img.shields.io/badge/buy%20me%20a%20coffee-donate-yellow.svg?style=for-the-badge
[codecov]: https://app.codecov.io/gh/golles/ha-tomtom-travel-time
[codecov-shield]: https://img.shields.io/codecov/c/github/golles/ha-tomtom-travel-time?style=for-the-badge
[commits-shield]: https://img.shields.io/github/commit-activity/y/golles/ha-tomtom-travel-time.svg?style=for-the-badge
[commits]: https://github.com/golles/ha-tomtom-travel-time/commits/main
[hacs]: https://github.com/custom-components/hacs
[hacs-shield]: https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge
[ha-active-installation-badges]: https://github.com/golles/ha-active-installation-badges
[hacs-installs-shield]: https://raw.githubusercontent.com/golles/ha-active-installation-badges/main/badges/tomtom_travel_time.svg
[license-shield]: https://img.shields.io/github/license/golles/ha-tomtom-travel-time.svg?style=for-the-badge
[maintainer]: https://github.com/golles
[maintenance-shield]: https://img.shields.io/badge/maintainer-golles-blue.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/golles/ha-tomtom-travel-time.svg?style=for-the-badge
[releases]: https://github.com/golles/ha-tomtom-travel-time/releases
[stars-shield]: https://img.shields.io/github/stars/golles/ha-tomtom-travel-time?style=for-the-badge
[stars]: https://github.com/golles/ha-tomtom-travel-time/stargazers
