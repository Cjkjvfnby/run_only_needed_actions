"""
Check the files were changed and set GitHub output values.
"""
import os
from argparse import ArgumentParser
from pathlib import Path
from subprocess import check_output

from check_file_changed._args import config_path
from check_file_changed._file_checker import WorkflowName, read_config
from check_file_changed._print import green, is_github, print_group, print_list


def get_changed_files(change: str, base: str) -> list[str]:
    cmd = ["git", "diff-tree", "--name-only", "-r", change, base]
    output = check_output(cmd)  # noqa: S603
    return output.decode().split("\n")


def get_output_text(
    all_workflows: list[WorkflowName],
    affected_workflows: set[WorkflowName],
) -> str:
    result = []

    for i, workflow in enumerate(all_workflows, start=1):
        detected = str(workflow in affected_workflows).lower()
        result.append(f"output-{i:>02}={detected}")
    return "\n".join(result)


def check_changed_files(
    *,
    config_file: str,
    change_ref: str,
    base_ref: str,
) -> None:
    file_checker = read_config(path=Path(config_file))

    with print_group("Template for workflow:"):
        print("=" * 50)
        print("jobs:")
        print("  detect-changed-files:")
        print("    runs-on: ubuntu-latest")
        print("    steps:")
        print("      - id: set-files-changed")
        print("        uses: cjkjvfnby/run_only_needed_actions@v1")
        print("        with:")
        print('          config-file: ".github/workflows/%s"' % Path(config_file).name)
        print("    outputs:")
        for i, wf in enumerate(file_checker.workflows, start=1):
            print(
                "      {}: ${{{{ steps.set-files-changed.outputs.output-{} }}}}".format(
                    wf,
                    str(i).zfill(2),
                ),
            )

        print("=" * 50)

    with print_group("Getting changed files"):
        changed_files = get_changed_files(change_ref, base_ref)
        print("\n".join(changed_files))

    with print_group("Detected file Groups"):
        raw_detected_groups = (
            file_checker.get_detected_group(path) for path in changed_files
        )
        detected_groups = {g for g in raw_detected_groups if g}

        print_list(detected_groups)

    affected_workflows = file_checker.get_workflows(detected_groups)

    print("Affected workflows:")
    print_list(affected_workflows)
    print()

    output_text = get_output_text(list(file_checker.workflows), affected_workflows)
    with print_group("Generated output"):
        print(output_text)

    if is_github():
        output_path = Path(os.environ["GITHUB_OUTPUT"])
        with output_path.open("a") as f:
            f.write(output_text)
    print(green("Done"))


def main() -> None:
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--change-ref", default="HEAD", help="The latest commit of PR")
    parser.add_argument(
        "--base-ref",
        default="HEAD^1",
        help="The latest commit of target branch (master)",
    )
    parser.add_argument("--config-file", default="config.toml", type=config_path)

    args = parser.parse_args()
    check_changed_files(
        config_file=args.config_file,
        change_ref=args.change_ref,
        base_ref=args.base_ref,
    )


if __name__ == "__main__":
    main()
