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
    if app_state.is_initialized and not session.get("authenticated"):
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
            success=True
        )
    return render_template("setup-config.html", title="Setup configuration")

@app.route(HOME)
def home():
    return "<p>Hello, World!</p>"

@app.route(LOGIN)
def login():
    return render_template("login.html", title="Login")

# API

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

if __name__ == "__main__":
    app.run(debug=True)
