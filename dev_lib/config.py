from .utils import *

# Definitions
FLASK_CONFIG_VALUES = {
    "DEBUG": bool,
    "SESSION_COOKIE_HTTPONLY": bool,
    "SESSION_COOKIE_SAMESITE": str,
    "SESSION_COOKIE_SECURE": bool,
    "TEMPLATES_AUTO_RELOAD": bool
}
APP_CONFIG_VALUES = {
    "version": str,
    "state_file_path": str,
    "snapshot_loc_path": str
}

def initialize_dependency(file_path: str, required_keys: dict[str, str]) -> dict:
    if not file_path:
        raise RuntimeError("Dependency file path not provided")
    path = format_path(file_path)
    if not path.exists():
        raise RuntimeError(f"Dependency file does not exist: {path}")
    data = load_json(path)
    validate_config(data, required_keys)
    return data

def validate_config(config: dict, required_keys: dict):
    errors = []
    for key, expected_type in required_keys.items():
        if key not in config:
            errors.append(f"Missing config key: {key}")
        elif not isinstance(config[key], expected_type):
            errors.append(
                f"{key} must be {expected_type.__name__}, "
                f"got {type(config[key]).__name__}"
            )
    if errors:
        raise RuntimeError(
            "Invalid flask_config.json:\n" + "\n".join(errors)
        )