"""
Sets the base configuration for the application.
"""

import os
from dataclasses import dataclass


CSV_PATH_VARNAME = "CSV_EXPORT_PATH"
CSV_DEF_PATH     = "exports/csv"


@dataclass
class BaseConfig:
    """
    Stores base configuration of application.

    Attributes:
        title (str): Title of the GUI Window
        geometry (str): Length and Width dimensions of Window
        font_family (str): Font Family for header
        header_font_size (int): Font Size for header
        header_font_style (str): Font Style for header
        csv_export_path (str): Configured Export Path of CSV
    """
    title:             str
    geometry:          str
    font_family:       str
    header_font_size:  int
    header_font_style: str
    csv_export_path:   str = CSV_DEF_PATH

    @staticmethod
    def get_env_var(var_name: str, default_value: str = "") -> str:
        """
        Retrieve an environment variable or fall back to a default value.
        Raises EnvironmentError if the variable is required and absent.

        Args:
            var_name (str): name of the env variable
            default_value (str): default value if env variable doesn't exist
        
        Returns:
            str: string of env variable
        """
        value = os.environ.get(var_name)
        if value is None and not default_value:
            raise EnvironmentError(f"Essential configuration '{var_name}' is missing")
        return value if value else default_value

    @classmethod
    def from_env(cls, **kwargs) -> "BaseConfig":
        """
        Resolves the CSV export path from the environment
        and merges it with any other keyword arguments.

        Args:
            cls (BaseConfig): reference to the class
            **kwargs: keyword arguments of base config
        
        Returns:
            BaseConfig: returns an instance of the BaseConfig with resolved csv path
        """
        csv_path = cls.get_env_var(CSV_PATH_VARNAME, CSV_DEF_PATH)
        return cls(csv_export_path=csv_path, **kwargs)