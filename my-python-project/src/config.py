import os
from pathlib import Path
import yaml
from dotenv import load_dotenv
from string import Template

class Config:
    def __init__(self):
        self._config = {}
        self._load_config()
        self._load_env()
        
        # Ensure logs directory exists
        self.logs_dir.mkdir(exist_ok=True)

    @property
    def project_root(self) -> Path:
        """Get the project root directory"""
        return Path(__file__).parent.parent

    def _load_config(self):
        """Load YAML configuration file"""
        config_path = self.project_root / 'config.yaml'
        
        with open(config_path, 'r') as f:
            # Load YAML first
            self._config = yaml.safe_load(f)
            
            # Handle variable substitution for paths
            if 'paths' in self._config:
                for key, value in self._config['paths'].items():
                    if isinstance(value, str):
                        self._config['paths'][key] = value.replace('${paths.data}', self._config['paths']['data'])

    def _load_env(self):
        """Load environment variables from .env file"""
        env_path = self.project_root / '.env'
        load_dotenv(env_path)

    def get(self, key, default=None):
        """Get a configuration value using dot notation"""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value

    def get_secret(self, key, default=None):
        """Get a secret from environment variables"""
        return os.getenv(key, default)

    @property
    def input_dir(self):
        return self.get('paths.input_dir')

    @property
    def output_dir(self):
        return self.get('paths.output_dir')

    @property
    def data_path(self):
        return self.get('paths.data')
        
    @property
    def logs_dir(self):
        """Get the logs directory path"""
        return self.project_root / 'logs'

# Create a global instance
config = Config()