import json
from pathlib import Path
from threading import Lock
from typing import Union, List
from schema.log_schema import SysLogEntry
import os

DATA_PATH = "./ai_host"
os.makedirs(DATA_PATH, exist_ok=True)

LOG_FILE = Path("./ai_host/system_logs.jsonl")
_lock = Lock()  # para evitar race conditions em escrita concorrente


class LogManager:

    @staticmethod
    def write_log(entry: Union[SysLogEntry, dict]):
        """Escreve um log no arquivo JSON."""
        if isinstance(entry, SysLogEntry):
            entry = entry.dict()

        # garante que sempre tenha timestamp em formato legível
        entry["date"] = entry["date"].isoformat()

        with _lock:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    @staticmethod
    def read_logs() -> List[dict]:
        """Lê todos os logs do arquivo."""
        if not LOG_FILE.exists():
            return []

        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return [json.loads(line) for line in f]

    @staticmethod
    def clear_logs():
        """Apaga todos os logs."""
        with _lock:
            LOG_FILE.write_text("", encoding="utf-8")