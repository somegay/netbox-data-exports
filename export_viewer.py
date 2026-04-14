from src.controllers.gui_controller import GuiController
from src.controllers.state_manager import StateManager
from src.controllers.base_config import BaseConfig

# GUI
TITLE = "Snapshot Viewer"
WINDOW_GEOMETRY = "960x540"
FONT_FAMILY = "Segoe UI"
FONT_SIZE_HEADER = 14
FONT_STYLE_HEADER = "bold"

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
        self.state_manager = StateManager(self.config.csv_export_path)
        # initialize GUI
        self.gui_controller = GuiController(
            self.state_manager,
            self.config)
        self.gui_controller.mainloop()

if __name__ == "__main__":
    Main()