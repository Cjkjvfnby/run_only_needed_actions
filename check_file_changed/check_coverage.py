"""
Check which files in the repo are covered.

It will help to have visibility over all files in the repo.
"""
import os
import re
import sys
from argparse import ArgumentParser
from pathlib import Path
from subprocess import check_output

from check_file_changed._args import config_path
from check_file_changed._file_checker import FileChecker, GroupName, read_config
from check_file_changed._print import green, print_group, print_list, red


def list_all_files(working_dir: Path) -> list[str]:
    cmd = ["git", "ls-tree", "--full-tree", "--name-only", "-r", "HEAD"]

    return (
        check_output(
            cmd,  # noqa: S603
            cwd=working_dir,
        )
        .decode()
        .strip()
        .split("\n")
    )


def check_patterns(config: FileChecker) -> int:
    unused_patterns = _get_unused_patterns(config)
    if not unused_patterns:
        print(green("All patterns are in use!"))
        return 0

    print(red(f"Found {len(unused_patterns)} unused patterns:"))
    for group, pattern in unused_patterns:
        print(red(f" - {group:<20} '{pattern.pattern}'"))
    return 2


def _get_unused_patterns(config: FileChecker) -> list[tuple[GroupName, re.Pattern]]:
    unused_patterns = []
    for group in config.groups:
        for pattern, count in group.matched.items():
            if count == 0:
                unused_patterns.append((group.name, pattern))
    return unused_patterns


def check_coverage(repo_root: Path, config_file: Path) -> None:
    file_checker = read_config(path=config_file)

    all_files = list_all_files(repo_root)

    missed_count = 0
    missed_files = []
    with print_group("Covered files"):
        print(f"{'path':<60}  {'group':<20} {'workflows'}")
        for path in all_files:
            result = file_checker.get_detected_group(path)
            if result:
                workflows = ", ".join(
                    sorted(file_checker.get_workflows([result])),
                )
                print(green(f"{path:<60}  {result:<20} {workflows}"))
            else:
                missed_count += 1
                missed_files.append(path)

    if missed_count:
        print(red(f"Missed files: {missed_count} from {len(all_files)}"))
        print_list(missed_files, color=red)
        exit_code = 1
    else:
        print(green("All files are covered!"))
        exit_code = 0

    check_exit = check_patterns(file_checker)
    sys.exit(exit_code + check_exit)


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--path-to-repo", default=os.curdir)
    parser.add_argument("--config-file", default="config.toml", type=config_path)
    args = parser.parse_args()

    check_coverage(Path(args.path_to_repo), Path(args.config_file))


if __name__ == "__main__":
    main()
