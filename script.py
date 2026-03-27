import requests, pandas, json, os, logging, logging.config
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configuration
def try_get_env_var(var_name: str, default_value: str = "") -> str:
    env_var_value = os.environ.get(var_name)
    if env_var_value is None and not default_value:
        raise EnvironmentError(f"Essential configuration {var_name} is missing")
    return env_var_value if env_var_value else default_value

load_dotenv()

DEFAULT_LOGGING_CONFIG_PATH = try_get_env_var("LOGGING_CONFIG_PATH", "logging_config.json")
DEFAULT_LOGS_OUTPUT_PATH = "logs"
try:
    NETBOX_URL = try_get_env_var("NETBOX_URL")
    NETBOX_TOKEN = try_get_env_var("NETBOX_TOKEN")
    NETBOX_ENDPOINTS = [
        {
            "name": "devices",
            "endpoint": "api/dcim/devices/"
        },
        {
            "name": "ip_addresses",
            "endpoint": "api/ipam/ip-addresses/"
        }
    ]
    HEADERS = {
        "Authorization": NETBOX_TOKEN,
        "Content-Type": "application/json"
    }
    CSV_EXPORT_PATH = try_get_env_var("CSV_EXPORT_PATH", "exports/csv")
    JSON_EXPORT_PATH = try_get_env_var("JSON_EXPORT_PATH", "exports/json")
except EnvironmentError:
    print(f"[INITIAL_CONFIG]: FATAL ERROR! - non-optional environmental variable is missing! Please check the documentation")
    exit(1)
except Exception as e:
    print(f"[INITIAL_CONFIG]: FATAL ERROR! - {e}")
    exit(1)

# Ensure logs output folder exists
base_path = Path(__file__).resolve().parent
logs_path = base_path / DEFAULT_LOGS_OUTPUT_PATH
logs_path.mkdir(parents=True, exist_ok=True)

# Load logging config
try:
    with open(DEFAULT_LOGGING_CONFIG_PATH, "r") as config_file:
        config_dict = json.loads(config_file.read())
        logging.config.dictConfig(config_dict)
except Exception as e:
    print(f"[INITIAL_CONFIG]: FATAL ERROR! - {e}")
    exit(1)

# Main Procedures

def fetch_dataset(headers: dict[str, str], netbox_url: str, endpoints: list[dict]) -> list[dict]:
    fetch_logger = logging.getLogger("script.fetch")
    fetch_logger.info("fetching data from endpoints..")
    # Auto-Retry
    session = requests.Session()
    retries = Retry(
        total=3, 
        backoff_factor=1, 
        status_forcelist=[502, 503, 504]
    )
    session.mount('https://', HTTPAdapter(max_retries=retries))
    datasets = []
    for endpoint in endpoints:
        fetch_logger.info(f'fetching data for netbox object {endpoint.get("name")}')
        base_url = netbox_url + endpoint.get("endpoint", "")
        combined_results = []
        current_url = base_url
        try:
            while current_url:
                fetch_logger.info(f'fetching data for current endpoint {endpoint.get("endpoint")}')
                response = session.get(current_url, headers=headers, timeout=30)
                response.raise_for_status()
                fetch_logger.info(f'successfuly received data for current endpoint{endpoint.get("endpoint")}')
                response_body = response.json()
                results = response_body.get("results")
                combined_results.extend(results)
                current_url = response_body.get("next")
            datasets.append({
                "name": endpoint.get("name", "unnamed_endpoint"),
                "data": combined_results
            })
        except requests.exceptions.RequestException:
            fetch_logger.error(f'failed fetching data for endpoint {endpoint.get("endpoint")}, moving on to next endpoint.')
            continue
    fetch_logger.info(f'data received for {len(datasets)} netbox objects')
    return datasets

def format_dataset(datasets: list[dict]) -> list[dict]:
    format_logger = logging.getLogger("script.format")
    format_logger.info("formatting dataset..")
    formatted_datasets = []
    for entry in datasets:
        name = entry.get("name", "")
        raw_data = entry.get("data", [])
        dataframe: pandas.DataFrame
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
    format_logger.info("successfuly formatted dataset")
    return formatted_datasets

def write_to_file(
        datasets: list[dict], 
        export_path: Path,  
        extension: str,
        datetime_now: str,
        write_callback: callable) -> None:
    write_logger = logging.getLogger("script.write")
    for dataset in datasets:
        name = dataset.get("name", "unknown")
        data = dataset.get("data", [])
        if data is None:
            write_logger.warning("dataset is empty, continuing to next dataset")
            continue # skip to next dataset if data is empty
        filename = f'{name}_export_{datetime_now}.{extension}'
        full_path = export_path / filename
        write_logger.info(f'attempting to write to file {filename}')
        try:
            write_callback(data, full_path)
        except Exception as e:
            write_logger.error(f'unexpected error occurred - {e}, continuing to next dataset')
            continue
        write_logger.info(f'writing to file {full_path} was successful!')

# Utility Functions

def get_datetime() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def get_export_path(export_path_str: str) -> Path:
    base_path = Path(__file__).resolve().parent
    export_path = base_path / export_path_str
    if not export_path.exists():
        export_path.mkdir(parents=True, exist_ok=True)
    return export_path

def write_to_csv(data: list, full_path: Path) -> None:
    data.to_csv(full_path, index=False)

def write_to_json(data: list, full_path: Path) -> None:
    with open(full_path, "w") as json_file:
        json.dump(data, json_file, indent=4, default=str)

# Entry

def main() -> None:
    script_logger = logging.getLogger("script")
    script_logger.info("starting script operations..")
    datetime_now = get_datetime()
    csv_export_path = get_export_path(Path(CSV_EXPORT_PATH))
    json_export_path = get_export_path(Path(JSON_EXPORT_PATH))
    try:
        datasets = fetch_dataset(HEADERS, NETBOX_URL, NETBOX_ENDPOINTS)
        if not datasets:
            return # handle if datasets is empty
        formatted_datasets = format_dataset(datasets)
        write_to_file(formatted_datasets, csv_export_path, "csv", datetime_now, write_to_csv)
        write_to_file(datasets, json_export_path, "json", datetime_now, write_to_json)
    except Exception as e:
        script_logger.critical(f'an unexpected error has occurred! exiting early..\n{e}')
        exit(1)
    script_logger.info("script run successful!")

if __name__ == "__main__":
    main()