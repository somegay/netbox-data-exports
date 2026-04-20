import bcrypt

def set_password(password: str) -> bool:
    """
    Hashes and stores the admin password in app_state.json.
    Returns True on success, False on failure.
    """
    if not password or not isinstance(password, str):
            return False
    try:
        # Hash password
        password_hash = hash_password(password)
        state = {}
        if APP_STATE_FILE.exists():
            with open(APP_STATE_FILE, "r", encoding="utf-8") as f:
                state = json.load(f)
        # Update password hash
        state["password_hash"] = password_hash
        tmp_file = APP_STATE_FILE.with_suffix(".tmp")
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
        tmp_file.replace(APP_STATE_FILE)
        return True
    except Exception:
        print("Error:", e)

def hash_password(password: str) -> bytes:
     return bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")