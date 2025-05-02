"""
Configuration management for PyKV
"""
import os
import json
from typing import Dict, Any


# Default configuration
DEFAULT_CONFIG = {
    "master_port": 3000,
    "volume_servers": [
        {"host": "localhost", "port": 3001, "weight": 1},
        {"host": "localhost", "port": 3002, "weight": 1},
    ],
    "replication_factor": 1,  # Number of copies to store (1 = no replication)
    "data_dir": "./data",
}


def load_config(config_path: str = None) -> Dict[str, Any]:
    """Load configuration from file or use defaults"""
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config
        except Exception as e:
            print(f"Error loading config: {e}")
            return DEFAULT_CONFIG
    else:
        return DEFAULT_CONFIG


def save_config(config: Dict[str, Any], config_path: str) -> bool:
    """Save configuration to file"""
    try:
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False 