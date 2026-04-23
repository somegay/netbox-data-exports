"""
Export selected NetBox objects to CSV and JSON formats.

This script authenticates against a NetBox instance, fetches 
objects via the Netbox REST API, and exports the results
to timestamped CSV and JSON files.
"""

import requests, pandas, json, os, logging, logging.config, sqlite3, argparse
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pydantic import BaseModel
from dataclasses import dataclass

# Config Definitions
@dataclass
class ScriptConfig:
    logging_config_path: str
    netbox_url: str
    netbox_token: str
    netbox_endpoints: list[dict]
    csv_export_path: str
    json_export_path: str
    headers: dict[str, str]

class AppConfig(BaseModel):
    version: str
    state_file_path: Path
    snapshot_loc_path: Path

class LoggingConfig(BaseModel):
    version: int
    disable_existing_loggers: bool
    formatters: dict
    handlers: dict
    loggers: dict

# Global Constants
SCRIPT_HELP = "Load all config from environment variables instead of the GUI state/config files"
SCRIPT_DESCRIPTION = "Export selected NetBox objects to CSV and JSON formats."
SCRIPT_DIR = Path(__file__).resolve().parent
TOOL_ARGS: argparse.Namespace = None
NETBOX_ENDPOINTS = [
    {
        "name": "devices",
        "endpoint": "/api/dcim/devices/"
    },
    {
        "name": "ip_addresses",
        "endpoint": "/api/ipam/ip-addresses/"
    }
]
DEFAULT_HEADERS = {
    "Authorization": "",
    "Content-Type": "application/json"
}

# Utility Functions
# --------------------------
def try_get_env_var(var_name: str, default_value: str = "") -> str:
    """
    Retrieve an environment variable or fallback to a default value.

    Raises an error if the variable is required and no default is provided.

    Args:
        var_name (str): Name of the environment variable.
        default_value (str): Optional fallback value.

    Returns:
        str: Environment variable value or default.
    """
    env_var_value = os.environ.get(var_name)
    if env_var_value is None and not default_value:
        raise EnvironmentError(f"Essential configuration {var_name} is missing")
    return env_var_value if env_var_value else default_value

def load_config_json(path: str) -> dict:
    """
    Loads JSON file into a dictionary safely.
    Fails fast if file is missing or if formatting or structure is invalid.

    Args:
        path (str): Path to the application configuration file.

    Returns:
        dict: Application configuration values.
    """
    try:
        # Checks file existence and JSON validity
        formatted_path = Path(path).resolve(strict=True)
        # Checks config structure validity
        with open(formatted_path, "r") as config_file:
            return json.load(config_file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in configuration file: {path}")
    except Exception as e:
        raise RuntimeError(f"Unexpected error loading configuration: {e}")

def list_to_string(datasets: dict[str, any]) -> str:
    names = [v for k, v in datasets.items() if k == "name"]
    return f"[{', '.join(names)}]"

# Main Procedures
# --------------------------

def parse_args() -> argparse.Namespace:
    parsers = argparse.ArgumentParser(description=SCRIPT_DESCRIPTION)
    parsers.add_argument(
        "--env",
        action="store_true",
        help=SCRIPT_HELP
    )
    return parsers.parse_args()

def create_config(args: argparse.Namespace) -> ScriptConfig:
    logging_config = try_get_env_var("LOGGING_CONFIG_PATH", "")
    logging_config_path = Path(logging_config).resolve(strict=True)
    if not TOOL_ARGS.env:
        # If --env flag is set, load all config from environment variables.
        try:
            app_config_path = try_get_env_var("APP_CONFIG", "")
            app_config = AppConfig.model_validate(load_config_json(app_config_path))
            export_path_csv = app_config.snapshot_loc_path / "csv"
            export_path_json = app_config.snapshot_loc_path / "json"
            
            # Load app state
            app_state_path = app_config.state_file_path
            if not app_state_path:
                raise RuntimeError("State file path is not provided in app configuration")
            formatted_app_state_path = Path(app_state_path).resolve(strict=True)
            
            # Attempt db connection
            conn = sqlite3.connect(str(formatted_app_state_path))
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM app_state WHERE id = 1").fetchone()
            conn.close()
            if row is None:
                raise RuntimeError(f"State database exists but contains no data: {formatted_app_state_path}")
            app_state = dict(row)

            # Set config values from env and db
            DEFAULT_HEADERS["Authorization"] = f"Token {app_state.get('netbox_token')}"
            script_config = ScriptConfig(
                logging_config_path=logging_config_path,
                netbox_url=app_state.get("netbox_url"),
                netbox_token=app_state.get("netbox_token"),
                netbox_endpoints=NETBOX_ENDPOINTS,
                csv_export_path=export_path_csv,
                json_export_path=export_path_json,
                headers=DEFAULT_HEADERS
            )
        except sqlite3.Error as e:
            print(f"[INITIAL_CONFIG]: FATAL ERROR! - Failed to read state database: {app_state_path} - {e}")
            exit(1)
        except Exception as e:
            print(f"[INITIAL_CONFIG]: FATAL ERROR! - {e}")
            exit(1)
    else:
        # Otherwise load config from app state and config files.
        try:
            # Set config values from env and db
            DEFAULT_HEADERS["Authorization"] = f"Token {app_state.get('netbox_token')}"
            script_config = ScriptConfig(
                logging_config_path=logging_config_path,
                netbox_url=try_get_env_var("NETBOX_URL", ""),
                netbox_token=try_get_env_var("NETBOX_TOKEN", ""),
                netbox_endpoints=NETBOX_ENDPOINTS,
                csv_export_path=try_get_env_var("CSV_EXPORT_PATH", ""),
                json_export_path=try_get_env_var("JSON_EXPORT_PATH", ""),
                headers=DEFAULT_HEADERS
            )
        except Exception as e:
            print(f"[INITIAL_CONFIG]: FATAL ERROR! - {e}")
            exit(1)

def setup_logging(logging_config_path: Path) -> None:
    try:
        with open(logging_config_path, "r") as config_file:
            config_dict = json.load(config_file.read())
            # Ensure the log directory exists before dictConfig tries to open
            for handler in config_dict.get("handlers", {}).values():
                log_file = handler.get("filename")
                if log_file:
                    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            
            # Apply logging configuration
            logging.config.dictConfig(config_dict)
    except Exception as e:
        print(f"[INITIAL_CONFIG]: FATAL ERROR! - {e}")
        exit(1)

def fetch_dataset(headers: dict[str, str], netbox_url: str, endpoints: list[dict]) -> list[dict]:
    """
    Fetch datasets for selected NetBox objects.

    Handles pagination and applies retry logic on transient failures.

    Args:
        headers (dict[str, str]): HTTP request headers.
        netbox_url (str): Base URL of the NetBox instance.
        endpoints (list[dict]): NetBox API endpoints to query.

    Returns:
        list[dict]: List of datasets, each containing a name and raw data.
    """

    # Setup logger
    fetch_logger = logging.getLogger("script.fetch")
    fetch_logger.info("fetching data from endpoints..")
    
    # Setup session
    session = requests.Session()
    retries = Retry(
        total=3,
        read=3,
        backoff_factor=1,
        status_forcelist=[502, 503, 504],
        allowed_methods=["GET"],
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    # Loop through endpoints to fetch them one by one
    datasets = []
    fetch_logger.info(f'fetching data for: [{
        ", ".join(endpoints)
        }]'
    )
    for endpoint in endpoints:
        base_url = netbox_url + endpoint.get("endpoint", "")
        fetch_logger.info(f'fetching data at {base_url}')
        # Create temporary list in case response body uses pagination for results
        combined_results = []
        current_url = base_url
        try:
            while current_url:
                fetch_logger.info(f'fetching data for current endpoint {current_url}')
                response = session.get(current_url, headers=headers, timeout=30)
                response.raise_for_status()
                fetch_logger.info(f'successfuly received data for current endpoint {current_url}')
                response_body = response.json()
                results = response_body.get("results")
                combined_results.extend(results)
                current_url = response_body.get("next")
            datasets.append({
                "name": endpoint.get("name", "unnamed_endpoint"),
                "data": combined_results
            })
        except requests.exceptions.RequestException:
            fetch_logger.error(f'failed fetching data for endpoint {current_url}, moving on to next endpoint.')
            continue
    fetch_logger.info(f'data received for {len(datasets)} netbox objects!')
    return datasets

def format_dataset(datasets: list[dict]) -> list[dict]:
    """
    Convert raw NetBox datasets into pandas DataFrames.

    Args:
        datasets (list[dict]): Raw datasets.

    Returns:
        list[dict]: Datasets containing DataFrames instead of raw JSON.
    """

    # Setup logger
    format_logger = logging.getLogger("script.format")
    format_logger.info("starting formatting operations..")
    
    # Loop through the results received in datasets
    formatted_datasets = []
    for entry in datasets:
        name = entry.get("name", "")
        raw_data = entry.get("data", [])
        dataframe: pandas.DataFrame
        format_logger.info(f"formatting dataset of object {name}")
        if not raw_data:
            format_logger.warning(f'dataset received is empty!')
            dataframe = pandas.DataFrame() 
        else:
            format_logger.info(f'flattening dataset {name} for csv..')
            dataframe = pandas.json_normalize(raw_data)
        formatted_datasets.append({
            "name": name,
            "data": dataframe
        })
        format_logger.info(f"successfuly formatted dataset of object {name}")
    format_logger.info(f"successfuly formatted datasets: {list_to_string(datasets)}]")
    return formatted_datasets

def write_to_files(datasets: list[dict], formatted_datasets: list[dict], script_config: ScriptConfig) -> None:

    """
    Write datasets to files using the provided writer callback.

    Args:
        datasets (list[dict]): Datasets to write.
        export_path (Path): Output directory.
        extension (str): File extension (csv or json).
        datetime_now (str): Timestamp included in filenames.
        write_callback (callable): Function that performs the write.
    """

    # Setup logger
    write_logger = logging.getLogger("script.writer")
    write_logger.log(f"Starting writing operations for datasets: {list_to_string(datasets)}")
    
    # loop through objects
    datetime_now = datetime.now()
    for dataset in datasets:
        name = dataset.get("name", "unknown")
        data = dataset.get("data", [])
        if data is None:
            write_logger.warning("dataset is empty, continuing to next dataset")
            continue # skip to next dataset if data is empty
        filename_csv = f'{name}_export_{datetime_now}.csv'
        filename_json = f'{name}_export_{datetime_now}.json'
        full_path_csv = script_config.csv_export_path / filename_csv
        full_path_json = script_config.json_export_path / filename_json
        write_logger.info(f'attempting to write to files {filename_csv}, {filename_json}')
        try:
            # Write to CSV
            write_logger.info(f'writing {filename_csv}..')
            formatted_datasets.to_csv(full_path_csv, index=False)
            write_logger.info(f'successfuly wrote {filename_csv}!')
            # Write to JSON
            write_logger.info(f'writing {filename_json}..')
            with open(full_path_json, "w") as json_file:
                json.dump(datasets, json_file, indent=4, default=str)
            write_logger.info(f'successfuly wrote {filename_json}!')
        except Exception as e:
            write_logger.error(f'unexpected error occurred - {e}, continuing to next dataset')
            continue
        write_logger.info(f'writing to files {filename_csv}, {filename_json} were successful!')

# Entry
# --------------------------
def main() -> None:
    """
    Entry point of script.
    """
    # Setup args
    TOOL_ARGS = parse_args()

    # Create config
    script_config = create_config(TOOL_ARGS)

    # Setup logging
    setup_logging(script_config.logging_config_path)

    # Main execution flow
    main_logger = logging.getLogger("script.main")
    #   1. Fetch dataset from Netbox API
    main_logger.info("starting main execution flow..")
    main_logger.info("fetching dataset from netbox api..")
    datasets = fetch_dataset(
        script_config.headers, 
        script_config.netbox_url, 
        script_config.netbox_endpoints
    )
    main_logger.info("datasets fetched successfully!")
    #   2. Format dataset for export
    main_logger.info("formatting datasets for export..")
    formatted_datasets = format_dataset(datasets)
    main_logger.info("formatting successful!")
    #   3. Write datasets to files
    main_logger.info("writing datasets to files..")
    write_to_files(datasets, formatted_datasets, script_config)
    main_logger.info("finished writing datasets to files!")
    main_logger.info("main execution flow finished successfully!")

if __name__ == "__main__":
    main()