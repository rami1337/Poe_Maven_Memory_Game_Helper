import json
import copy
import os

APP_NAME = "PoE Maven Memory Game Helper"
APPDATA_DIR = os.getenv('APPDATA')
CONFIG_DIR = os.path.join(APPDATA_DIR, APP_NAME)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

DEFAULT_CONFIG = {
    "hotkeys": {
        'Sequence 1': 'f1',
        'Sequence 2': 'f2',
        'Sequence 3': 'f3',
        'Clear Sequence': 'f4',
        'Toggle Overlay': 'f5',
    },
    "sequence_actions": {
        'Sequence 1': 'Left',
        'Sequence 2': 'Top',
        'Sequence 3': 'Right',
    },
    "style": {
        "font_colors": {
            'Sequence 1': '#ffffff',
            'Sequence 2': '#ffffff',
            'Sequence 3': '#ffffff',
        },
        "background_color": "black",
        "font_size": 24,
        "separator": " -> ",
        "x": "center",
        "y": 20
    }
}

def load_config():
    """Loads configuration, merging saved settings with defaults."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            saved_config = json.load(f)
            config = copy.deepcopy(DEFAULT_CONFIG)
            for key, value in saved_config.items():
                if isinstance(value, dict) and key in config:
                    config[key].update(value)
                else:
                    config[key] = value
            return config
    except (FileNotFoundError, json.JSONDecodeError):
        return copy.deepcopy(DEFAULT_CONFIG)

def save_config(config):
    """Saves configuration to a JSON file."""
    try:
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
    except OSError:
        # Failed to create the directory, so don't proceed.
        return

    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)
