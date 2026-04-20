from pathlib import Path
import json

def load_json(path: Path) -> dict:
    try:
        with path.open() as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON in {path}") from e

def initialize_file(file: str):
    formatted_path = format_path(file)
    try:
        formatted_path.mkdir(parents=True, exist_ok=True)
        return formatted_path.open()
    except Exception as e:
        print (f"Error: {e}")

def format_path(path: str) -> Path:
    try:
        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj
        return Path().cwd() / path_obj
    except Exception as e:
        print(f"Error: {e}")