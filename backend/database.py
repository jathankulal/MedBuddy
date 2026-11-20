"""JSON persistence helpers with safe creation, reading, and atomic writing."""

import json
import os
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any


def _json_default(o):
    """JSON serializer for date/datetime objects."""
    if isinstance(o, (date, datetime)):
        return o.isoformat()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


def ensure_data_dir(data_dir: str = "./data") -> Path:
    """Create the data directory if it does not exist. Returns the directory path."""
    path = Path(data_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def data_file_path(data_dir: str, filename: str) -> Path:
    """Return the full path for a data file inside the data directory."""
    return Path(data_dir) / filename


def read_json(data_dir: str, filename: str, default: Any = None) -> Any:
    """Read and parse a JSON file.

    Returns ``default`` when the file does not exist.
    """
    path = Path(data_dir) / filename
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def write_json(data_dir: str, filename: str, data: Any) -> None:
    """Atomically write JSON data to a file.

    Writes to a temporary file in the same directory then atomically replaces
    the target, so readers never see a partially written file.
    """
    path = Path(data_dir) / filename
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, ensure_ascii=False, default=_json_default)
            fh.write("\n")
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
