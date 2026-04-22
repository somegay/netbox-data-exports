"""
reset_db.py — resets the app state to factory defaults for testing.

Usage:
    python reset_db.py --db /path/to/app_state.db

This wipes is_initialized, hashed_password, netbox_url, and netbox_token
back to their defaults. The database file and table are left intact.
"""

import argparse
import sqlite3
import sys
from pathlib import Path

RESET = """
UPDATE app_state
SET is_initialized  = 0,
    hashed_password = '',
    netbox_url      = '',
    netbox_token    = '',
    auth_version    = 0
WHERE id = 1;
"""

def reset_db(db_path: Path) -> None:
    if not db_path.exists():
        print(f"Database not found at '{db_path}'. Has init_db.py been run?")
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(RESET)
        conn.commit()
        print(f"State reset to factory defaults in '{db_path}'.")
    except Exception as e:
        conn.rollback()
        print(f"Error during reset: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reset Netbox Manager app state for testing.")
    parser.add_argument("--db", required=True, help="Path to the SQLite database file to reset.")
    args = parser.parse_args()
    reset_db(Path(args.db))