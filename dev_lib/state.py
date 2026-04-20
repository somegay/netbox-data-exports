from .utils import *

class AppState:
    def __init__(self, state_path: Path, **app_config):
        self.state_path = state_path
        self.is_initialized = app_config.get("is_initialized", False)
        self.hashed_password = app_config.get("hashed_password", "")
        self.netbox_url = app_config.get("netbox_url", "")
        self.netbox_token = app_config.get("netbox_token", "")

    def save(self):
        state_data = {
            "is_initialized": self.is_initialized,
            "hashed_password": self.hashed_password,
            "netbox_url": self.netbox_url,
            "netbox_token": self.netbox_token
        }
        try:
            with open(self.state_path, "w") as f:
                json.dump(state_data, f)
        except OSError:
            print("Error saving state, please check file permissions.")

def initialize_state(state_file_path: str) -> AppState:
    formatted_path = format_path(state_file_path)
    if not formatted_path.exists():
        raise RuntimeError("State file not found, initializing new state file.")
    state_data = load_json(formatted_path)
    return AppState(formatted_path, **state_data)