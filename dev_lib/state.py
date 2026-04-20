from .utils import *

class AppState:
    def __init__(self, **app_config):
        self.is_initialized = app_config.get("is_initialized", False)
        self.hashed_password = app_config.get("hashed_password", "")
        self.netbox_url = app_config.get("netbox_url", "")
        self.netbox_token = app_config.get("netbox_token", "")

def initialize_state(state_file_path: str) -> AppState:
    formatted_path = format_path(state_file_path)
    if not formatted_path.exists():
        raise RuntimeError("State file not found, initializing new state file.")
    state_data = load_json(formatted_path)
    return AppState(**state_data)