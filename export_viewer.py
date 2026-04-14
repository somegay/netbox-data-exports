from src.controllers.gui_controller import GuiController
from src.controllers.state_manager import StateManager
from src.controllers.base_config import BaseConfig
from pathlib import Path

# GUI
TITLE = "Snapshot Viewer"
WINDOW_GEOMETRY = "960x540"
FONT_FAMILY = "Segoe UI"
FONT_SIZE_HEADER = 14
FONT_STYLE_HEADER = "bold"
# PATH
DEFAULT_EXPORT_PATH = "exports/csv"

class Main:
    def __init__(self):
        # Initialize Config
        self.config = BaseConfig({
            "title": TITLE,
            "geometry": WINDOW_GEOMETRY,
            "font_family": FONT_FAMILY,
            "header_font_size": FONT_SIZE_HEADER,
            "header_font_style": FONT_STYLE_HEADER
        })
        # initialize State Manager
        self.state_manager = StateManager(set_snapshot_path(DEFAULT_EXPORT_PATH))
        # initialize GUI
        self.gui_controller = GuiController(
            self.state_manager,
            self.config)
        self.gui_controller.mainloop()

def set_snapshot_path(exports_path):
    base_path = Path(__file__).resolve().parent
    return base_path / exports_path

if __name__ == "__main__":
    Main()