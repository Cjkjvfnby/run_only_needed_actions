import re
from pathlib import Path, PurePath
from textwrap import dedent
from tomllib import loads

import pytest

from check_file_changed._file_checker import (
    ConfigError,
    FileChecker,
    FileGroup,
    GroupName,
    _read_config_from_data,
    read_config,
)

"""
[workflow]
workflow_readme = ["readme"]
workflow_workflow_yml = ["workflow_yml"]
workflow_support =  ["readme", "workflow_yml"]
workflow_all = ["all"]

[group.readme]
examples = ['README.md']
patterns = ['^README.md$']

[group.workflow_yml]
examples = ["", ""]
patterns = ['']


[group.all]
examples = ["check_file_changed/config.toml"]
patterns = ['.*']
"""


def test_config_could_be_read():
    res = read_config(
        Path(__file__).parent.parent / "check_file_changed" / "config.toml",
    )
    assert res.workflows == {
        "workflow_readme": {"readme"},
        "workflow_workflow_yml": {"workflow_yml"},
        "workflow_support": {"readme", "workflow_yml"},
        "workflow_all": {"all"},
    }
    assert res.groups == [
        FileGroup(
            name=GroupName("readme"),
            examples=[PurePath("README.md")],
            patterns=[re.compile(r"^README.md$", re.IGNORECASE)],
        ),
        FileGroup(
            name=GroupName("workflow_yml"),
            examples=[
                PurePath(".github/workflows/check.yml"),
                PurePath(".github/workflows/run_on_push.yml"),
            ],
            patterns=[re.compile(r"^\.github/workflows/.*\.yml$", re.IGNORECASE)],
        ),
        FileGroup(
            name=GroupName("all"),
            examples=[
                PurePath("check_file_changed/config.toml"),
            ],
            patterns=[re.compile(r".*", re.IGNORECASE)],
        ),
    ]


def _parse_toml_from_string(s: str) -> dict:
    return loads(dedent(s))


@pytest.fixture()
def checker() -> FileChecker:
    toml = """
        [workflow]
        workflow_a = ["a"]
        workflow_b = ["b"]
        workflow_ab = ["a", "b"]

        [group.a]
        examples = ["file_a"]
        patterns = ['file_a']

        [group.b]
        examples = ["file_b"]
        patterns = ['file_b']
        """
    return _read_config_from_data(_parse_toml_from_string(toml))


def test_file_could_be_detected(checker: FileChecker):
    assert checker.get_detected_group("file_a") == GroupName("a")


def test_file_could_not_be_detected(checker: FileChecker):
    assert checker.get_detected_group("unknown") is None


@pytest.mark.parametrize(
    ("groups", "workflows"),
    [
        ({GroupName("a")}, {"workflow_a", "workflow_ab"}),
        ({GroupName("b")}, {"workflow_b", "workflow_ab"}),
        ({GroupName("a"), GroupName("b")}, {"workflow_a", "workflow_b", "workflow_ab"}),
    ],
)
def test_checker_workflow_could_be_detected(
    groups: set[GroupName],
    workflows: set[str],
    checker: FileChecker,
):
    assert checker.get_workflows(groups) == workflows


def _error_id(item):
    if item.startswith(("\n", "[")):
        return "config"
    return item.lower().replace(" ", "-").replace("'", "").replace(":", "")


@pytest.mark.parametrize(
    ("conf", "message_regexp"),
    [
        (
            "[group.a]",
            "Expect only 'workflow' and 'group' toplevel sections",
        ),
        (
            "[workflow]",
            "Expect only 'workflow' and 'group' toplevel sections",
        ),
        (
            """
                [workflow]
                [group.a]
                [extra]

                """,
            "Expect only 'workflow' and 'group' toplevel sections",
        ),
        (
            """
                [workflow]
                [group.a]
                patterns = ['file_a']
                """,
            "Expect only 'examples' and 'patterns'",
        ),
        (
            """
                [workflow]
                [group.a]
                examples = ['file_a']
                """,
            "Expect only 'examples' and 'patterns'",
        ),
        (
            """
                [workflow]
                [group.a]
                examples = ['file_a']
                patterns = ['file_a']
                extra = ['hello']
                """,
            "Expect only 'examples' and 'patterns'",
        ),
        (
            """
                [workflow]
                [group.a]
                examples = []
                patterns = ['file_a']
                """,
            "Examples could not be empty for group: a",
        ),
        (
            """
                [workflow]
                [group.a]
                examples = ["file_a"]
                patterns = []
                """,
            "Patterns could not be empty for group: a",
        ),
        (
            """
                [workflow]
                [group.a]
                examples = ["file_a"]
                patterns = ["file_b"]
                """,
            "'a' example 'file_a' does not match any pattern:",
        ),
        (
            """
                [workflow]
                wa = ["a", "b"]
                [group.a]
                examples = ["file_a"]
                patterns = ["file_a"]
                """,
            "Workflow 'wa' has unknown groups: b",
        ),
        (
            """
                [workflow]
                wa = ["a"]
                [group.a]
                examples = ["file_a"]
                patterns = ["file_a"]

                [group.unused]
                examples = ["unused"]
                patterns = ["unused"]
                """,
            "Unused groups: unused",
        ),
    ],
    ids=_error_id,
)
def test_parsing_errors(conf, message_regexp):
    with pytest.raises(ConfigError, match=message_regexp):
        _read_config_from_data(_parse_toml_from_string(conf))
