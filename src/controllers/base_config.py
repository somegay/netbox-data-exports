import os
from dotenv import load_dotenv

CSV_PATH_VARNAME = "CSV_EXPORT_PATH"
CSV_DEF_PATH = "exports/csv"

class BaseConfig:
    def __init__(self, 
                 config):
        load_dotenv()
        self.title = config["title"]
        self.geometry = config["geometry"]
        self.csv_export_path = self.try_get_env_var(CSV_PATH_VARNAME, CSV_DEF_PATH)
        self.font_family = config["font_family"]
        self.header_font_size = config["header_font_size"]
        self.header_font_style = config["header_font_style"]
    
    def try_get_env_var(self, var_name: str, default_value: str = "") -> str:
        """
        Retrieve an environment variable or fallback to a default value.

        Raises an error if the variable is required and no default is provided.

        Args:
            var_name (str): Name of the environment variable.
            default_value (str): Optional fallback value.

        Returns:
            str: Environment variable value or default.
        """
        env_var_value = os.environ.get(var_name)
        if env_var_value is None and not default_value:
            raise EnvironmentError(f"Essential configuration {var_name} is missing")
        return env_var_value if env_var_value else default_value
