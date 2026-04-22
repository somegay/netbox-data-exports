"""
setup.py: interactive first-time installer for Netbox Manager.

Run once from the project root after cloning:
    python setup/setup.py

What it does:
  1. Asks where each config file should live (with sensible defaults).
  2. Asks for Flask and app configuration values.
  3. Writes all config files to the chosen locations.
  4. Writes a .env file at the project root so app.py can find them.
  5. Initialises the SQLite state database via the init_db logic.

Re-running is safe: existing files are shown to the user and they are
asked whether to overwrite before anything is touched.
"""

import json
import os
import secrets
import sqlite3
import sys
from pathlib import Path

# Helpers
# ---------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _header(title: str) -> None:
    print()
    print("─" * 60)
    print(f"  {title}")
    print("─" * 60)


def _ask(prompt: str, default: str) -> str:
    """Prompt the user for input, returning default on empty reply."""
    value = input(f"  {prompt} [{default}]: ").strip()
    return value if value else default


def _ask_bool(prompt: str, default: bool) -> bool:
    hint = "Y/n" if default else "y/N"
    raw = input(f"  {prompt} [{hint}]: ").strip().lower()
    if not raw:
        return default
    return raw in ("y", "yes")


def _resolve(raw: str) -> Path:
    """Resolve a path relative to the project root."""
    p = Path(raw)
    if not p.is_absolute():
        p = PROJECT_ROOT / p
    return p.resolve()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _ensure_dir(path: Path) -> None:
    """Create a directory (and any missing parents) if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def _confirm_overwrite(path: Path) -> bool:
    """If the file already exists, ask the user whether to overwrite it."""
    if not path.exists():
        return True
    print(f"\n  Warning: '{path}' already exists.")
    return _ask_bool("Overwrite?", default=False)


def _write_json(path: Path, data: dict) -> None:
    _ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"  ✔  Written: {path}")


def _write_text(path: Path, content: str) -> None:
    _ensure_parent(path)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✔  Written: {path}")


# DB init
# ---------------------

_DDL = """
CREATE TABLE IF NOT EXISTS app_state (
    id               INTEGER PRIMARY KEY CHECK (id = 1),
    is_initialized   INTEGER NOT NULL DEFAULT 0,
    hashed_password  TEXT    NOT NULL DEFAULT '',
    netbox_url       TEXT    NOT NULL DEFAULT '',
    netbox_token     TEXT    NOT NULL DEFAULT '',
    auth_version     INTEGER NOT NULL DEFAULT 0
);
"""

_SEED = """
INSERT OR IGNORE INTO app_state
    (id, is_initialized, hashed_password, netbox_url, netbox_token, auth_version)
VALUES (1, 0, '', '', '', 0);
"""


def _init_db(db_path: Path) -> None:
    _ensure_parent(db_path)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(_DDL)
        conn.execute(_SEED)
        conn.commit()
        print(f"  ✔  Database initialised: {db_path}")
    except Exception as e:
        db_path.unlink(missing_ok=True)
        raise RuntimeError(f"Database initialisation failed: {e}") from e
    finally:
        conn.close()


# Steps
# ---------------------

def step_file_locations() -> dict:
    """Ask the sysadmin where each file should live."""
    _header("Step 1 of 4 — File locations")
    print("  Press Enter to accept the default path shown in brackets.\n")

    locations = {}

    locations["env"] = _resolve(_ask(".env file",                   ".env"))
    locations["flask_config"] = _resolve(_ask("Flask config   (JSON)",       "config/flask_config.json"))
    locations["app_config"] = _resolve(_ask("App config     (JSON)",       "config/app_config.json"))
    locations["logging_config"] = _resolve(_ask("Logging config (JSON)",       "config/logging_config.json"))
    locations["state_db"] = _resolve(_ask("State database (SQLite .db)", "data/state.db"))
    locations["snapshot_dir"] = _resolve(_ask("Snapshots directory",         "exports"))
    locations["log_dir"] = _resolve(_ask("Log file directory",          "logs"))

    print()
    print("  Locations chosen:")
    for key, path in locations.items():
        print(f"    {key:<20} {path}")

    if not _ask_bool("\n  Confirm and continue?", default=True):
        print("  Aborted.")
        sys.exit(0)

    return locations


def step_flask_config(locations: dict) -> None:
    """Build and write flask_config.json."""
    _header("Step 2 of 4 — Flask configuration")
    print("  Defaults are production-safe. Press Enter to accept.\n")

    debug = _ask_bool("DEBUG mode", default=False)
    secure_cookie = _ask_bool("SESSION_COOKIE_SECURE (HTTPS only)", default=False)
    samesite = _ask("SESSION_COOKIE_SAMESITE (Lax/Strict/None)", default="Lax")
    auto_reload = _ask_bool("TEMPLATES_AUTO_RELOAD", default=False)

    flask_cfg = {
        "DEBUG": debug,
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": samesite,
        "SESSION_COOKIE_SECURE": secure_cookie,
        "TEMPLATES_AUTO_RELOAD": auto_reload,
    }

    path = locations["flask_config"]
    if not _confirm_overwrite(path):
        print("  Skipped.")
        return

    _write_json(path, flask_cfg)


def step_app_config(locations: dict) -> None:
    """Build and write app_config.json."""
    _header("Step 3 of 4 — App configuration")
    print("  Paths below are derived from your choices in Step 1.\n")

    # Paths are already decided — just show them for confirmation
    state_db_path   = locations["state_db"]
    snapshot_path   = locations["snapshot_dir"]

    print(f"    state_file_path   : {state_db_path}")
    print(f"    snapshot_loc_path : {snapshot_path}")

    app_cfg = {
        "version": "0.1",
        "state_file_path": state_db_path.as_posix(),   # forward slashes — safe on Windows
        "snapshot_loc_path": snapshot_path.as_posix(),
    }

    path = locations["app_config"]
    if not _confirm_overwrite(path):
        print("  Skipped.")
        return

    _write_json(path, app_cfg)


def step_logging_config(locations: dict) -> None:
    """Build and write logging_config.json."""
    _header("Step 3b — Logging configuration")
    print("  Log rotation: daily, kept for 30 days.\n")

    log_file = locations["log_dir"] / "script.log"
    print(f"    Log file : {log_file}")

    logging_cfg = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "[%(name)s]: %(levelname)s - %(message)s"
            },
            "standard": {
                "format": "%(asctime)s [%(name)s]: %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            }
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "stream": "ext://sys.stdout"
            },
            "file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "level": "DEBUG",
                "formatter": "standard",
                "filename": log_file.as_posix(),  # forward slashes — safe on Windows and avoids JSON escape issues
                "when": "midnight",
                "interval": 7,
                "backupCount": 30,
                "encoding": "utf-8"
            }
        },
        "loggers": {
            "": {
                "level": "DEBUG",
                "handlers": ["stdout", "file"],
                "propagate": "false"
            }
        }
    }

    path = locations["logging_config"]
    if not _confirm_overwrite(path):
        print("  Skipped.")
        return

    _write_json(path, logging_cfg)


def step_env_and_db(locations: dict) -> None:
    """Write .env, initialise the database, and create runtime directories."""
    _header("Step 4 of 4 — Environment file and database")

    # Generate a secure Flask secret key automatically
    secret_key = secrets.token_hex(32)
    print("  A random FLASK_SECRET_KEY has been generated for you.")
    print("  Keep it secret — changing it will invalidate all active sessions.\n")

    # Use forward slashes for all paths in .env — backslashes are treated as
    # escape characters by python-dotenv and will corrupt paths on Windows.
    env_lines = [
        "# Generated by setup.py — do not commit this file to version control.",
        f'FLASK_SECRET_KEY="{secret_key}"',
        f'FLASK_CONFIG="{locations["flask_config"].as_posix()}"',
        f'APP_CONFIG="{locations["app_config"].as_posix()}"',
        f'LOGGING_CONFIG_PATH="{locations["logging_config"].as_posix()}"',
    ]
    env_content = "\n".join(env_lines) + "\n"

    env_path = locations["env"]
    if _confirm_overwrite(env_path):
        _write_text(env_path, env_content)
    else:
        print("  Skipped .env — app.py will use the existing file.")

    # Database
    db_path = locations["state_db"]
    if db_path.exists():
        print(f"\n  Database already exists at '{db_path}'.")
        if not _ask_bool("  Re-initialise? (this will NOT wipe existing data)", default=False):
            print("  Skipped database.")
        else:
            _init_db(db_path)
    else:
        _init_db(db_path)

    # Create runtime directories that are never written to during setup but
    # must exist before the app starts (exports/snapshots and log output).
    print()
    for key in ("snapshot_dir", "log_dir"):
        dir_path = locations[key]
        _ensure_dir(dir_path)
        print(f"  ✔  Directory ready: {dir_path}")


# Entry point 
# ---------------------

def main() -> None:
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║          Netbox Manager — First-time Setup               ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"\n  Project root: {PROJECT_ROOT}\n")
    print("  This script will write config files, a .env file, and")
    print("  initialise the SQLite state database.")
    print("  Existing files will not be overwritten without confirmation.")

    if not _ask_bool("\n  Ready to begin?", default=True):
        print("  Aborted.")
        sys.exit(0)

    try:
        locations = step_file_locations()
        step_flask_config(locations)
        step_app_config(locations)
        step_logging_config(locations)
        step_env_and_db(locations)
    except KeyboardInterrupt:
        print("\n\n  Setup interrupted.")
        sys.exit(1)
    except RuntimeError as e:
        print(f"\n  Error: {e}")
        sys.exit(1)

    _header("Setup complete")
    print(" You can schedule the export automation script with your operating system's task scheduler \n(e.g. cron on Linux or Task Scheduler on Windows).")
    print("  You can now start the app with your preferred WSGI server, for example:")
    print()
    print("      gunicorn app:app")
    print()
    print("  To reset app state for testing:")
    print()
    print(f"      python setup/reset_db.py --db \"{locations['state_db']}\"")
    print()


if __name__ == "__main__":
    main()