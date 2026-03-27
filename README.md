# Netbox Object Export Automation Script
This script automates the exporting of Netbox's IP allocations and devices daily in both CSV and JSON formats.

## Prerequisites
- Python 3.12+
- A Virtual Environment is highly recommended to isolate dependencies and prevent global package pollution.

### Dependency Installation
In order to install the packages use:
```bash
pip install -r requirements.txt
```
> **Note**:
> Any python package manager can be used so long as they can parse the `requirements.txt` file

## Configuration
This script uses environmental variables to configure its behavior, below is a table containing all the definitions used:
| Variable  | Description  | Optional? | Sample Value |
|---|---|---|---|
| NETBOX_TOKEN  | contains auth token for netbox instance  | no | 'Token a2rsk211' |
| NETBOX_URL  | contains base URL netbox instance  | no | 'https://instance.netbox.com' |
| LOGGING_CONFIG_PATH  | path to logging configuration definition  | yes | 'logging_config.json' |
| CSV_EXPORT_PATH  | path to csv exports location  | yes | 'exports/csv' |
| JSON_EXPORT_PATH  | path to JSON exports location  | yes | 'exports/json' |

> **Note**:
> The format for `NETBOX_TOKEN` varies between versions
> Refer to the [official Netbox API documentation](https://netboxlabs.com/docs/netbox/integrations/rest-api/) for more information:

#### Logging Configuration
The script comes with a default logging configuration file. This will output logs through the:
- standard terminal output
- files
You are free to configure the logging mechanism as needed, following [python's dict logging](https://docs.python.org/3/library/logging.config.html) configuration standards. 

## Usage
Execute the script using the Python interpreter
```bash
python3 script.py
```

## Outputs
The script will create three additional directories:
- logs
- CSV exports
- JSON exports

*Logs*: Contains operational history. The default configuration rotates logs weekly, retaining a backup of the last 30 instances before automatically deleting the oldest instances.

**CSV Exports**: Contains tabular data for `devices` and `IP addresses`.

**JSON Exports**: Contains raw JSON for `devices` and `IP addresses`.

> **Note**:
> All exported files follow the format: `[object_name]_[datetime].[format]`
> Ex: `devices_12-2-5_5:23:12.csv`