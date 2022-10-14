import json
from pathlib import Path


class Config:
    # DEFAULT_PATH = Path.home() / ".gtaskconfig.json"
    DEFAULT_PATH = Path(".gtaskconfig.json")

    def __init__(self) -> None:
        if not self.DEFAULT_PATH.exists():
            raise RuntimeError("The configuration file is needed")

        with open(str(self.DEFAULT_PATH), "r") as f:
            self._config: dict = json.load(f)

        self._task_list_id: str = self._config["default_list_id"]

    @property
    def config(self) -> dict:
        return self._config

    @property
    def task_list_id(self) -> str:
        return self._task_list_id

    @task_list_id.setter
    def task_list_id(self, val) -> None:
        self._config["default_list_id"] = val
        self._write_config_to_file()

    def _write_config_to_file(self) -> None:
        with open(str(self.DEFAULT_PATH), "w") as f:
            json.dump(self._config, f)
