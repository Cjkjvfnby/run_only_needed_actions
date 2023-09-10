import os
from collections.abc import Callable, Collection, Iterator
from contextlib import contextmanager
from typing import NewType


def is_github() -> bool:
    return os.environ.get("GITHUB_ACTIONS") == "true"


Color = NewType("Color", int)


def template(color: int) -> str:
    return f"\033[{color}m"


_end = template(0)
_red = template(31)
_green = template(32)


def green(line: str) -> str:
    return f"{_green}{line}{_end}"


def red(line: str) -> str:
    return f"{_red}{line}{_end}"


@contextmanager
def print_group(title: str) -> Iterator[None]:
    if is_github():
        print(f"::group::{title}")
    else:
        print(f"{title}:")
    yield None
    print()
    if is_github():
        print("::endgroup::")


def print_list(items: Collection[str], color: Callable[[str], str] = green) -> None:
    for i in sorted(items):
        print(f" - {color(i)}")
