"""
Simple GUI for viewing exported Netbox Object data.
"""

from pathlib import Path
from dotenv import load_dotenv

from app.base_config import BaseConfig
from app.state_manager import StateManager
from app.gui_controller import GuiController

# GUI configuration

TITLE             = "Snapshot Viewer"
WINDOW_GEOMETRY   = "960x540"
FONT_FAMILY       = "Segoe UI"
FONT_SIZE_HEADER  = 14
FONT_STYLE_HEADER = "bold"
DEFAULT_EXPORT_PATH = "exports/csv"


class Main:
    """
    Entry point to the application.
    """
    def __init__(self):
        load_dotenv()

        base_path   = Path(__file__).resolve().parent
        export_path = base_path / DEFAULT_EXPORT_PATH

        self.config = BaseConfig.from_env(
            title=TITLE,
            geometry=WINDOW_GEOMETRY,
            font_family=FONT_FAMILY,
            header_font_size=FONT_SIZE_HEADER,
            header_font_style=FONT_STYLE_HEADER,
        )
        self.state_manager  = StateManager(export_path)
        self.gui_controller = GuiController(self.state_manager, self.config)

    def run(self) -> None:
        self.gui_controller.mainloop()


if __name__ == "__main__":
    Main().run()