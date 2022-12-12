import json
import sys
from pathlib import Path

import pydantic


class AuthConfig(pydantic.BaseModel):
    token_path: str
    client_secret_path: str


class ConfigData(pydantic.BaseModel):
    default_list_id: str
    auth: AuthConfig


class Config:
    _DEFAULT_FILE_NAME = ".gtasksrc.json"
    _DEFAULT_PATH_HOME = Path.home() / _DEFAULT_FILE_NAME
    _DEFAULT_PATH_LOCAL = Path(_DEFAULT_FILE_NAME)

    def __init__(self) -> None:

        # We expect the config file either in the home directory or in the local directory
        # (from where the command is called)
        self._config_file_path: Path = self._get_gtasksrc_path()

        try:
            self._config: ConfigData = ConfigData.parse_file(str(self._config_file_path))
        except FileNotFoundError:
            print("[*] You need to create a config file - please check the README (e.g.: touch $HOME/.gtasksrc.json)")
            sys.exit(1)

        # Parse the file immediately
        self._client_secret_file_path: Path = Path(self._config.auth.client_secret_path)
        self._token_file_path: Path = Path(self._config.auth.token_path)
        self._task_list_id: str = self._config.default_list_id

    def _get_gtasksrc_path(self) -> Path:
        if self._DEFAULT_PATH_HOME.exists():
            return self._DEFAULT_PATH_HOME
        elif not self._DEFAULT_PATH_LOCAL.exists():
            return self._DEFAULT_PATH_LOCAL
        else:
            raise RuntimeError(f"The configuration file {self._DEFAULT_FILE_NAME} is not found")

    @property
    def config(self) -> ConfigData:
        return self._config

    @property
    def task_list_id(self) -> str:
        return self._task_list_id

    @task_list_id.setter
    def task_list_id(self, val) -> None:
        self._config.default_list_id = val
        self._write_config_to_file()

    @property
    def client_secret_path(self) -> Path:
        if self._client_secret_file_path.exists():
            return self._client_secret_file_path
        else:
            raise FileNotFoundError("The client_secret.json is not found")

    @property
    def token_path(self) -> Path:
        return self._token_file_path

    def _write_config_to_file(self) -> None:
        with open(str(self._config_file_path), "w") as f:
            json.dump(self._config.dict(), f)
        print(f"The {self._DEFAULT_FILE_NAME} file is updated. (full path: {self._config_file_path}")
