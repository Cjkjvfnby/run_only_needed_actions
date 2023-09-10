import re
from collections import Counter
from collections.abc import Collection
from dataclasses import dataclass
from pathlib import Path, PurePath
from tomllib import load
from typing import NamedTuple, NewType

WorkflowName = NewType("WorkflowName", str)
GroupName = NewType("GroupName", str)


class ConfigError(Exception):
    """
    Exception for config validation errors.
    """


@dataclass
class FileGroup:
    name: GroupName
    examples: list[PurePath]
    patterns: list[re.Pattern]

    def __init__(
        self,
        name: GroupName,
        examples: list[PurePath],
        patterns: list[re.Pattern],
    ):
        self.name = name
        self.examples = examples
        self.patterns = patterns
        self.matched = Counter({x: 0 for x in patterns})

        super().__init__()

    def accept(self, path: PurePath) -> bool:
        posix_path = path.as_posix()

        for pattern in self.patterns:
            if pattern.search(posix_path):
                self.matched[pattern] += 1
                return True
        return False


class FileChecker(NamedTuple):
    workflows: dict[WorkflowName, set[GroupName]]
    groups: list[FileGroup]

    def get_detected_group(self, path: str) -> GroupName | None:
        for group in self.groups:
            if group.accept(PurePath(path)):
                return group.name
        return None

    def get_workflows(self, groups: Collection[GroupName]) -> set[WorkflowName]:
        return {
            w
            for w, workflow_groups in self.workflows.items()
            if workflow_groups.intersection(groups)
        }


def _extract_workflows(param: dict) -> dict[WorkflowName, set[GroupName]]:
    return {WorkflowName(k): {GroupName(x) for x in v} for k, v in param.items()}


def _extract_groups(param: dict) -> list[FileGroup]:
    groups = []
    for name, group_data in param.items():
        if set(group_data) != {"examples", "patterns"}:
            msg = f"Expect only 'examples' and 'patterns' got {set(group_data)} for [group.{name}]"
            raise ConfigError(msg)

        if not group_data["examples"]:
            msg = f"Examples could not be empty for group: {name}"
            raise ConfigError(msg)

        if not group_data["patterns"]:
            msg = f"Patterns could not be empty for group: {name}"
            raise ConfigError(msg)

        examples = [PurePath(x) for x in group_data["examples"]]

        patterns = [re.compile(x, flags=re.IGNORECASE) for x in group_data["patterns"]]

        groups.append(FileGroup(GroupName(name), examples, patterns))
    return groups


def read_config(path: Path) -> FileChecker:
    with path.open("rb") as f:
        data = load(f)

    return _read_config_from_data(data)


def _read_config_from_data(data: dict) -> FileChecker:
    if set(data) != {"workflow", "group"}:
        msg = "Expect only 'workflow' and 'group' toplevel sections"
        raise ConfigError(msg)

    workflows = _extract_workflows(data["workflow"])
    groups = _extract_groups(data["group"])
    _validate(workflows, groups)
    return FileChecker(workflows, groups)


def _validate(
    workflows: dict[WorkflowName, set[GroupName]],
    groups: list[FileGroup],
) -> None:
    _validat_examples_match_patterns(groups)

    all_groups = {group.name for group in groups}

    for workflow, workflow_groups in workflows.items():
        if not workflow_groups.issubset(all_groups):
            msg = f"Workflow '{workflow}' has unknown groups: {', '.join(sorted(workflow_groups - all_groups))}"
            raise ConfigError(msg)

    all_used_groups = {
        group for workflow_groups in workflows.values() for group in workflow_groups
    }
    if not all_groups.issubset(all_used_groups):
        msg = f"Unused groups: {', '.join(sorted(all_groups - all_used_groups))}"
        raise ConfigError(msg)


def _validat_examples_match_patterns(groups: list[FileGroup]) -> None:
    for group in groups:
        for example in group.examples:
            if not group.accept(example):
                msg = f"'{group.name}' example '{example.as_posix()}' does not match any pattern: {group.patterns}"
                raise ConfigError(msg)
