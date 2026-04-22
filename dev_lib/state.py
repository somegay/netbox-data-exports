import sqlite3
from .utils import *
from .auth import verify_password, hash_password, valid_password

# ── Expected schema ───────────────────────────────────────
# These are the columns the app requires to be present in app_state.
# If any are missing, the app refuses to start — schema drift is a
# sysadmin concern, not something the app silently works around.

_REQUIRED_COLUMNS = {
    "id",
    "is_initialized",
    "hashed_password",
    "netbox_url",
    "netbox_token",
    "auth_version",
}

# ── Helpers ───────────────────────────────────────────────

def _connect(db_path: Path) -> sqlite3.Connection:
    """
    Open a WAL-mode connection.
    check_same_thread=False is safe here because all writes are
    serialized via BEGIN IMMEDIATE — no two writers can proceed
    simultaneously regardless of which thread they're on.
    """
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def _validate_schema(conn: sqlite3.Connection) -> None:
    """
    Verify that app_state exists and contains every required column.
    Raises RuntimeError with a clear message if validation fails so
    initialize_state() can surface it to the sysadmin at boot time.
    """
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='app_state'"
    ).fetchone()

    if row is None:
        raise RuntimeError(
            "Table 'app_state' not found. "
            "Has init_db.py been run against this database?"
        )

    columns = {
        col["name"]
        for col in conn.execute("PRAGMA table_info(app_state)").fetchall()
    }
    missing = _REQUIRED_COLUMNS - columns
    if missing:
        raise RuntimeError(
            f"Schema validation failed — missing columns: {', '.join(sorted(missing))}. "
            "Re-run init_db.py or apply the required migrations."
        )


def _read_row(conn: sqlite3.Connection) -> sqlite3.Row:
    return conn.execute("SELECT * FROM app_state WHERE id = 1").fetchone()


# ── AppState ──────────────────────────────────────────────

class AppState:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._conn = _connect(db_path)
        row = _read_row(self._conn)

        # Expose attributes so app.py read-access stays identical
        self.is_initialized  = bool(row["is_initialized"])
        self.hashed_password = row["hashed_password"]
        self.netbox_url      = row["netbox_url"]
        self.netbox_token    = row["netbox_token"]
        self.auth_version    = row["auth_version"]

    # ── Atomic transactions ───────────────────────────────

    def get_auth_version(self) -> int:
        """
        Read auth_version directly from the DB, bypassing the in-process
        attribute. Called by the guard on every request so it always reflects
        the true current value across all workers.
        """
        row = self._conn.execute(
            "SELECT auth_version FROM app_state WHERE id = 1"
        ).fetchone()
        return row["auth_version"]

    def setup_password(self, new_password: str) -> tuple[bool, str]:
        """
        First-time setup: hash and store a new password, mark app as initialized.
        Returns (success, error_message).
        """
        if not valid_password(new_password):
            return False, "Invalid password"

        hashed = hash_password(new_password)

        with self._conn:
            self._conn.execute("BEGIN IMMEDIATE")
            self._conn.execute(
                """UPDATE app_state
                      SET hashed_password = ?,
                          is_initialized  = 1,
                          auth_version    = auth_version + 1
                    WHERE id = 1""",
                (hashed,)
            )

        self.hashed_password = hashed
        self.is_initialized  = True
        self.auth_version   += 1
        return True, ""

    def change_password(self, current_password: str, new_password: str) -> tuple[bool, str]:
        """
        Atomically verify the current password and replace it.
        The write lock is acquired before the read, so no two workers
        can race through the verify-then-write window simultaneously.
        Returns (success, error_message).
        """
        if not current_password or not new_password:
            return False, "Invalid payload"

        if not valid_password(new_password):
            return False, "Invalid new password"

        with self._conn:
            self._conn.execute("BEGIN IMMEDIATE")  # lock acquired before the read
            row = _read_row(self._conn)

            if not verify_password(current_password, row["hashed_password"]):
                return False, "Current password is incorrect"

            hashed = hash_password(new_password)
            self._conn.execute(
                """UPDATE app_state
                      SET hashed_password = ?,
                          auth_version    = auth_version + 1
                    WHERE id = 1""",
                (hashed,)
            )

        self.hashed_password = hashed
        self.auth_version   += 1
        return True, ""

    def save_netbox_config(self, netbox_url: str, netbox_token: str) -> tuple[bool, str]:
        """
        Atomically replace NetBox credentials.
        Returns (success, error_message).
        """
        with self._conn:
            self._conn.execute("BEGIN IMMEDIATE")
            self._conn.execute(
                "UPDATE app_state SET netbox_url = ?, netbox_token = ? WHERE id = 1",
                (netbox_url, netbox_token)
            )

        self.netbox_url   = netbox_url
        self.netbox_token = netbox_token
        return True, ""

    def clear_netbox_config(self) -> tuple[bool, str]:
        """
        Atomically wipe NetBox credentials.
        Returns (success, error_message).
        """
        with self._conn:
            self._conn.execute("BEGIN IMMEDIATE")
            self._conn.execute(
                "UPDATE app_state SET netbox_url = '', netbox_token = '' WHERE id = 1"
            )

        self.netbox_url   = ""
        self.netbox_token = ""
        return True, ""


# ── Initialization ────────────────────────────────────────

def initialize_state(state_file_path: str) -> AppState:
    """
    Drop-in replacement for the old initialize_state().

    Expects the DB to already exist and be provisioned by init_db.py.
    Validates connectivity and schema on startup — raises RuntimeError
    with a clear message if either check fails, halting the app boot.
    """
    db_path = format_path(state_file_path)

    if not db_path.exists():
        raise RuntimeError(
            f"State database not found at '{db_path}'. "
            "Run init_db.py to provision it before starting the app."
        )

    conn = _connect(db_path)
    try:
        _validate_schema(conn)
    finally:
        conn.close()

    return AppState(db_path)