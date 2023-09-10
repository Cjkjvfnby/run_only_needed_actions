from argparse import ArgumentTypeError
from pathlib import Path


def config_path(path_string: str) -> Path:
    path = Path(path_string)
    if path.exists():
        return path
    msg = f"file {path_string} does not exists"
    raise ArgumentTypeError(msg)
