from pathlib import Path
from typing import Dict

import yaml


def load_config(config_path: str) -> Dict:
    path = Path(config_path)
    try:
        content = path.read_text(encoding="utf-8")
    except FileNotFoundError as error:
        raise ValueError(f"Configuration file not found: {path}") from error
    except OSError as error:
        raise ValueError(f"Cannot read configuration file {path}: {error}") from error

    try:
        config = yaml.safe_load(content)
    except yaml.YAMLError as error:
        raise ValueError(f"Invalid YAML in configuration file {path}: {error}") from error

    if not isinstance(config, dict):
        raise ValueError(f"Configuration file {path} must contain a YAML mapping")

    required_sections = {"testing", "ammeters", "result_management"}
    missing = sorted(required_sections - config.keys())
    if missing:
        raise ValueError(
            f"Configuration file {path} is missing sections: {', '.join(missing)}"
        )
    return config
