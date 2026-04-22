from flask import Flask, jsonify, redirect, request, render_template, session, url_for
from dotenv import load_dotenv
from dev_lib.utils import *
from dev_lib.config import *
from dev_lib.state import *
from dev_lib.auth import *
import os, requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

load_dotenv()

# ── NetBox HTTP session ───────────────────────────────────

def _netbox_session() -> requests.Session:
    """
    Returns a requests Session configured for NetBox Cloud's free tier,
    which sleeps after inactivity and can take >10s to cold-start.

    Strategy:
      - Generous timeout (30s) to survive the cold-start wake-up window.
      - 3 retries with exponential backoff (1s, 2s, 4s) for transient
        network errors and bad-gateway responses from the sleeping host.
      - Read timeouts are retried explicitly via Retry(read=3) since
        urllib3 does not count them against `total` by default.
    """
    session = requests.Session()
    retry = Retry(
        total=3,
        read=3,
        backoff_factor=1,           # waits: 1s, 2s, 4s between retries
        status_forcelist=[502, 503, 504],
        allowed_methods=["GET", "POST"],
        raise_on_status=False,
    )
    session.mount("https://", HTTPAdapter(max_retries=retry))
    session.mount("http://",  HTTPAdapter(max_retries=retry))
    return session

NETBOX_TIMEOUT = 30  # seconds — wide enough to cover a cold-start wake-up

# Config locations
FLASK_CONFIG_PATH = os.environ.get("FLASK_CONFIG")
APP_CONFIG_PATH = os.environ.get("APP_CONFIG")

# Initialize app
print("checking dependencies..")
flask_config = initialize_dependency(FLASK_CONFIG_PATH, FLASK_CONFIG_VALUES)
app_config = initialize_dependency(APP_CONFIG_PATH, APP_CONFIG_VALUES)
app = Flask(__name__)

# Apply config
print("applying config..")
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-only-unsafe")
app.config.from_mapping(flask_config)

# Initialize state file
app_state = initialize_state(app_config.get("state_file_path"))

# Endpoints
STATIC = "/static"
HOME = "/"
SETUP = "/auth/setup"
INIT_CONFIG_SETUP = "/initialize-config"
LOGIN = "/auth/login"

@app.before_request
def guard():
    if request.path.startswith(STATIC):
        return
    if request.path.startswith(SETUP):
        return
    if app_state.is_initialized and request.path == SETUP:
        return redirect(HOME)
    if not app_state.is_initialized and request.path != SETUP:
        return redirect(SETUP)
    if app_state.is_initialized and request.path != LOGIN:
        # Check session auth_version against DB on every request.
        # If the password changed since this session was created, the
        # version won't match and the session is invalidated immediately,
        # kicking all browsers that aren't holding the new password.
        db_version = app_state.get_auth_version()
        if session.get("auth_version") != db_version:
            session.clear()
            return redirect(LOGIN)
        if request.path != LOGIN and not session.get("authenticated"):
            return redirect(LOGIN)

@app.route(SETUP, methods=["GET", "POST"])
def setup():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        password = data.get("password")

        # Atomically validates, hashes, and persists the password in one transaction
        success, error = app_state.setup_password(password)
        if not success:
            return jsonify(success=False, message=error), 400

        session["authenticated"] = True
        session["auth_version"]  = app_state.auth_version
        return jsonify(
            success=True,
            next=url_for("init_config_setup")
        )
    return render_template("password-setup.html", title="Setup password")


@app.route(INIT_CONFIG_SETUP, methods=["GET", "POST"])
def init_config_setup():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        if "netbox_url" not in data or "netbox_token" not in data:
            return jsonify(success=False, message="Invalid payload"), 400

        # Atomically persists both credentials together
        app_state.save_netbox_config(data["netbox_url"], data["netbox_token"])

        return jsonify(
            success=True,
            next=url_for("home")
        )
    return render_template("setup-config.html", title="Setup configuration")

@app.route(LOGIN, methods=["GET", "POST"])
def login():
    if session.get("authenticated"):
        return redirect(url_for("home"))
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        password = data.get("password")

        if not password:
            return jsonify(success=False, message="Password required"), 400

        if not verify_password(password, app_state.hashed_password):
            return jsonify(success=False, message="Invalid password"), 401

        session["authenticated"] = True
        session["auth_version"]  = app_state.auth_version
        return jsonify(success=True, next=url_for("home"))

    return render_template("login.html", title="Login")

# ── Shareable view helpers ────────────────────────────────

def _fetch_live_data():
    """Fetch live devices + IPs from NetBox. Returns (devices, ips, error)."""
    if not app_state.netbox_url or not app_state.netbox_token:
        return [], [], "NetBox is not configured."

    headers = {
        "Authorization": f"Token {app_state.netbox_token}",
        "Accept": "application/json",
    }

    try:
        nb = _netbox_session()
        dev_r = nb.get(
            f"{app_state.netbox_url}/api/dcim/devices/?limit=1000",
            headers=headers, timeout=NETBOX_TIMEOUT,
        )
        ip_r = nb.get(
            f"{app_state.netbox_url}/api/ipam/ip-addresses/?limit=1000",
            headers=headers, timeout=NETBOX_TIMEOUT,
        )
        dev_r.raise_for_status()
        ip_r.raise_for_status()
    except requests.RequestException as e:
        return [], [], str(e)

    devices = []
    for d in dev_r.json().get("results", []):
        devices.append({
            "name": d.get("name", "Unnamed device"),
            "type": (
                (d.get("role") or {}).get("name")
                or (d.get("device_type") or {}).get("model")
                or "Device"
            ),
            "status": (
                (d.get("status") or {}).get("label")
                or (d.get("status") or {}).get("value")
                or "Unknown"
            ),
            "site": ((d.get("site") or {}).get("name") or "—"),
            "manufacturer": (
                ((d.get("device_type") or {})
                 .get("manufacturer") or {})
                .get("name", "—")
            ),
            "model": (d.get("device_type") or {}).get("model", "—"),
            "ip_address": (
                (d.get("primary_ip4") or {}).get("address")
                or (d.get("primary_ip") or {}).get("address")
                or "—"
            ),
            "description": d.get("description") or "",
        })

    ips = []
    for ip in ip_r.json().get("results", []):
        ips.append({
            "address": ip.get("address", "—"),
            "status": (
                (ip.get("status") or {}).get("label")
                or (ip.get("status") or {}).get("value")
                or "Unknown"
            ),
            "assigned_to": (
                (ip.get("assigned_object") or {}).get("name")
                or (ip.get("assigned_object") or {}).get("display")
                or "Unassigned"
            ),
            "vrf": ((ip.get("vrf") or {}).get("name") or "Global"),
            "tenant": ((ip.get("tenant") or {}).get("name") or "—"),
            "description": ip.get("description") or "",
        })

    return devices, ips, None


def _load_snapshot_data(snapshot_id):
    """Load a snapshot from CSV files. Returns (devices, ips, error)."""
    base = Path(app_config.get("snapshot_loc_path")) / "csv"
    devices_path = base / f"devices_export_{snapshot_id}.csv"
    ips_path = base / f"ip_addresses_export_{snapshot_id}.csv"

    if not devices_path.exists() and not ips_path.exists():
        return None, None, f"Snapshot '{snapshot_id}' not found."

    devices = load_devices_csv(devices_path) if devices_path.exists() else []
    ips = load_ips_csv(ips_path) if ips_path.exists() else []
    return devices, ips, None


# ── Page routes ───────────────────────────────────────────

@app.route(HOME)
def home():
    return render_template("index.html", title="Dashboard",
                           initial_source=None, initial_data=None)


@app.route("/live")
def view_live():
    devices, ips, error = _fetch_live_data()
    initial_data = {
        "source": "live",
        "devices": devices,
        "ip_addresses": ips,
        "error": error or "",
    }
    return render_template("index.html", title="Live Objects — Netbox Manager",
                           initial_source="live", initial_data=initial_data)


@app.route("/snapshot/<snapshot_id>")
def view_snapshot(snapshot_id):
    devices, ips, error = _load_snapshot_data(snapshot_id)

    if error:
        return render_template("index.html", title="Snapshot Not Found — Netbox Manager",
                               initial_source=snapshot_id,
                               initial_data={"source": snapshot_id, "devices": [], "ip_addresses": [], "error": error})

    initial_data = {
        "source": snapshot_id,
        "devices": devices,
        "ip_addresses": ips,
        "error": "",
    }
    return render_template("index.html", title=f"Snapshot {snapshot_id} — Netbox Manager",
                           initial_source=snapshot_id, initial_data=initial_data)


# ── API ───────────────────────────────────────────────────

@app.route("/api/test-netbox", methods=["POST"])
def test_netbox():
    cfg = request.get_json()
    try:
        r = _netbox_session().get(
            f"{cfg['netbox_url']}/api/",
            headers={
                "Authorization": f"Token {cfg['netbox_token']}",
                "Accept": "application/json",
            },
            timeout=NETBOX_TIMEOUT,
        )
        if r.status_code == 200:
            return jsonify({"ok": True})

        return jsonify({
            "error": f"NetBox returned HTTP {r.status_code}"
        }), 400
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/auth/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/api/live/devices")
def api_live_devices():
    if not app_state.netbox_url or not app_state.netbox_token:
        return jsonify(
            success=False,
            error="NetBox is not configured."
        ), 400
    r = _netbox_session().get(
        f"{app_state.netbox_url}/api/dcim/devices/?limit=1000",
        headers={
            "Authorization": f"Token {app_state.netbox_token}",
            "Accept": "application/json",
        },
        timeout=NETBOX_TIMEOUT,
    )
    r.raise_for_status()

    raw = r.json().get("results", [])
    devices = []

    for d in raw:
        devices.append({
            "name": d.get("name", "Unnamed device"),
            "type": (
                (d.get("role") or {}).get("name")
                or (d.get("device_type") or {}).get("model")
                or "Device"
            ),
            "status": (
                (d.get("status") or {}).get("label")
                or (d.get("status") or {}).get("value")
                or "Unknown"
            ),
            "site": ((d.get("site") or {}).get("name") or "—"),
            "manufacturer": (
                ((d.get("device_type") or {})
                 .get("manufacturer") or {})
                .get("name", "—")
            ),
            "model": (d.get("device_type") or {}).get("model", "—"),
            "ip_address": (
                (d.get("primary_ip4") or {}).get("address")
                or (d.get("primary_ip") or {}).get("address")
                or "—"
            ),
            "description": d.get("description") or "",
        })

    return jsonify(devices)


@app.route("/api/live/ips")
def api_live_ips():
    if not app_state.netbox_url or not app_state.netbox_token:
        return jsonify(
            success=False,
            error="NetBox is not configured."
        ), 400
    r = _netbox_session().get(
        f"{app_state.netbox_url}/api/ipam/ip-addresses/?limit=1000",
        headers={
            "Authorization": f"Token {app_state.netbox_token}",
            "Accept": "application/json",
        },
        timeout=NETBOX_TIMEOUT,
    )
    r.raise_for_status()

    raw = r.json().get("results", [])
    ips = []

    for ip in raw:
        ips.append({
            "address": ip.get("address", "—"),
            "status": (
                (ip.get("status") or {}).get("label")
                or (ip.get("status") or {}).get("value")
                or "Unknown"
            ),
            "assigned_to": (
                (ip.get("assigned_object") or {}).get("name")
                or (ip.get("assigned_object") or {}).get("display")
                or "Unassigned"
            ),
            "vrf": ((ip.get("vrf") or {}).get("name") or "Global"),
            "tenant": ((ip.get("tenant") or {}).get("name") or "—"),
            "description": ip.get("description") or "",
        })

    return jsonify(ips)

@app.route("/api/snapshots")
def api_list_snapshots():
    base = Path(app_config.get("snapshot_loc_path")) / "csv"
    return jsonify(list_snapshots(base))

@app.route("/api/snapshots/<snapshot_id>")
def api_load_snapshot(snapshot_id):
    base = Path(app_config.get("snapshot_loc_path")) / "csv"

    devices_path = base / f"devices_export_{snapshot_id}.csv"
    ips_path = base / f"ip_addresses_export_{snapshot_id}.csv"

    data = {}

    if devices_path.exists():
        data["devices"] = load_devices_csv(devices_path)
    else:
        data["devices"] = []

    if ips_path.exists():
        data["ip_addresses"] = load_ips_csv(ips_path)
    else:
        data["ip_addresses"] = []

    return jsonify(data)


@app.route("/api/netbox/config", methods=["GET", "DELETE"])
def get_netbox_config_metadata():
    if request.method == "DELETE":
        # Atomically wipes both fields together
        app_state.clear_netbox_config()
        return jsonify(success=True)

    return jsonify({
        "url": app_state.netbox_url,
        "configured": bool(app_state.netbox_token),
    })

@app.route("/api/auth/change-password", methods=["POST"])
def change_password():
    if not session.get("authenticated"):
        return jsonify(success=False, message="Not authenticated"), 401

    data = request.get_json(silent=True) or {}

    # Atomically verifies current password and replaces it in one transaction
    success, error = app_state.change_password(
        data.get("currentPassword"),
        data.get("newPassword"),
    )

    if not success:
        status = 403 if error == "Current password is incorrect" else 400
        return jsonify(success=False, message=error), status

    session.clear()
    return jsonify(success=True)

if __name__ == "__main__":
    app.run(debug=True)