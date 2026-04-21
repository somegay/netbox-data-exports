from flask import Flask, jsonify, redirect, request, render_template, session, url_for
from dotenv import load_dotenv
from dev_lib.utils import *
from dev_lib.config import *
from dev_lib.state import *
from dev_lib.auth import *
import os, requests

load_dotenv()

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
    if app_state.is_initialized and not session.get("authenticated") and request.path != LOGIN:
        return redirect(LOGIN)

@app.route(SETUP, methods=["GET", "POST"])
def setup():
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        password = data.get("password")
        if not valid_password(password):
            return jsonify(success=False, message="Invalid password"), 400
        app_state.hashed_password = hash_password(password)
        app_state.is_initialized = True
        app_state.save()
        session["authenticated"] = True
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
        app_state.netbox_url = data.get("netbox_url")
        app_state.netbox_token = data.get("netbox_token")
        app_state.save()
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
        return jsonify(success=True, next=url_for("home"))

    return render_template("login.html", title="Login")

@app.route(HOME)
def home():
    return render_template("index.html", title="dashboard")

# API
# ---------------------------

@app.route("/api/test-netbox", methods=["POST"])
def test_netbox():
    cfg = request.get_json()
    try:
        r = requests.get(
            f"{cfg['netbox_url']}/api/",
            headers={
                "Authorization": f"Token {cfg['netbox_token']}",
                "Accept": "application/json",
            },
            timeout=5,
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

from flask import jsonify
import requests

@app.route("/api/live/devices")
def api_live_devices():
    if not app_state.netbox_url or not app_state.netbox_token:
        return jsonify(
            success=False,
            error="NetBox is not configured."
        ), 400
    r = requests.get(
        f"{app_state.netbox_url}/api/dcim/devices/?limit=1000",
        headers={
            "Authorization": f"Token {app_state.netbox_token}",
            "Accept": "application/json",
        },
        timeout=10,
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
    r = requests.get(
        f"{app_state.netbox_url}/api/ipam/ip-addresses/?limit=1000",
        headers={
            "Authorization": f"Token {app_state.netbox_token}",
            "Accept": "application/json",
        },
        timeout=10,
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
        app_state.netbox_url = ""
        app_state.netbox_token = ""
        app_state.save()
        return jsonify(success=True)

    return jsonify({
        "url": app_state.netbox_url,
        "configured": bool(app_state.netbox_token),
    })

@app.route("/api/auth/change-password", methods=["POST"])
def change_password():
    # 1. Must be authenticated
    if not session.get("authenticated"):
        return jsonify(success=False, message="Not authenticated"), 401

    data = request.get_json(silent=True) or {}
    current = data.get("currentPassword")
    new = data.get("newPassword")

    if not current or not new:
        return jsonify(success=False, message="Invalid payload"), 400

    # 2. Verify current password
    if not verify_password(current, app_state.hashed_password):
        return jsonify(success=False, message="Current password is incorrect"), 403

    # 3. Validate new password
    if not valid_password(new):
        return jsonify(success=False, message="Invalid new password"), 400

    # 4. Save new password
    app_state.hashed_password = hash_password(new)
    app_state.save()

    # 5. Force logout
    session.clear()
    return jsonify(success=True)

if __name__ == "__main__":
    app.run(debug=True)
