"""
init_db.py — run once during installation to provision the SQLite state database.

Usage:
    python init_db.py --db /path/to/state.db

The path should match the value of `state_file_path` in your app config.
"""

import argparse
import sqlite3
import sys
from pathlib import Path

DDL = """
CREATE TABLE IF NOT EXISTS app_state (
    id               INTEGER PRIMARY KEY CHECK (id = 1),
    is_initialized   INTEGER NOT NULL DEFAULT 0,
    hashed_password  TEXT    NOT NULL DEFAULT '',
    netbox_url       TEXT    NOT NULL DEFAULT '',
    netbox_token     TEXT    NOT NULL DEFAULT '',
    auth_version     INTEGER NOT NULL DEFAULT 0
);
"""

SEED = """
INSERT OR IGNORE INTO app_state (id, is_initialized, hashed_password, netbox_url, netbox_token, auth_version)
VALUES (1, 0, '', '', '', 0);
"""

def init_db(db_path: Path) -> None:
    if db_path.exists():
        print(f"Database already exists at {db_path}. Nothing to do.")
        sys.exit(0)

    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(DDL)
        conn.execute(SEED)
        conn.commit()
        print(f"Database initialized at {db_path}")
    except Exception as e:
        db_path.unlink(missing_ok=True)
        print(f"Error during initialization: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize the Netbox Manager state database.")
    parser.add_argument("--db", required=True, help="Path to the SQLite database file to create.")
    args = parser.parse_args()
    init_db(Path(args.db))