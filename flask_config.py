import os
from pathlib import Path

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Runtime directory (mutable)
APP_STATE_FILE = BASE_DIR / "app_config.json"

# Flask configuration
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-only-unsafe")

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False  # set True when behind HTTPS

# Flask behavior
TEMPLATES_AUTO_RELOAD = False