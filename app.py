from flask import Flask, redirect, request, render_template
from dotenv import load_dotenv
from dev_lib.utils import *
from dev_lib.config import *
from dev_lib.state import *
import os

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
SETUP = "/setup"

@app.route("/")
def home():
    return "<p>Hello, World!</p>"

if __name__ == "__main__":
    app.run(debug=True)
