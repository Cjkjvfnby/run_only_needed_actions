[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Actions status](https://github.com/Cjkjvfnby/run_only_needed_actions/actions/workflows/check.yml/badge.svg)](https://github.com/Cjkjvfnby/run_only_needed_actions/actions)
[![Actions status](https://github.com/Cjkjvfnby/run_only_needed_actions/actions/workflows/run_on_push_v1.yml/badge.svg)](https://github.com/Cjkjvfnby/run_only_needed_actions/actions)
[![Actions status](https://github.com/Cjkjvfnby/run_only_needed_actions/actions/workflows/run_on_push.yml/badge.svg)](https://github.com/Cjkjvfnby/run_only_needed_actions/actions)

# Run Only Needed Actions v1


The Action to run subworkflows on condition when something is changed.

## Who might need this:
- You have multiple workflows in your GitHub repository.
- Actions take time/resources to run.
- It makes sense for run only some workflow when file is changed, but rules for that is complicated for [paths|paths-ignore][1].
- You make workflow mandatory. Because when you skip workflow via path to ignore, it's not counted as passed.


## How
You write a config that lists which files should trigger witch workflow and use it with this action.


## TL;DR;
- [config sample][config_toml]
- [workflow sample][workflow]
- Copy-paste and run.
  - Do not forget to change `master` to `v1`
  - Code have a bunch of checks, just see errors in logs before reading the documentation.


## Config file format
Config uses 2 layer configuration.

On the top level you define a workflow and names of the file groups are related to it.
On the bottom there are file groups that match specific files.

A simple map between name and list of groups.
Name could be any, groups are name that present in the groups section.

```toml
[workflow]
workflow_a = ["file_a"]
workflow_b = ["file_a"]
workflow_c = ["file_b", "file_c"]
```

On the bottom there are groups. Each group catches a files that matches the regexps.
Order matters! File a handled by the first group it matches.

```toml
[group.file_a]
examples = ["check_file_changed/config.toml"]
patterns = ['.*']

[group.file_b]
examples = ['README.md']
patterns = ['^README.md$']

[group.file_c]
examples = [".github/workflows/check.yml", ".github/workflows/run_on_push.yml"]
patterns = ['^\.github/workflows/.*\.yml$']
```

Section `[group.<name>]`, where name should be present at least in a single workflow

- `examples` is a list of paths in the posix style with "/" as separators.
   This examples are for readability and automated checks, that are performed when script run.
   There is no check that these files are actually exists.
- `patterns` list of patterns that should match this group. [Python regular expression syntax][re] is used.
   Use single quotes for regular expressions, in that case you won't need to escape backslashes `\\`.
   Pattern is [matched][re.search] to any position in the path, so if you want to match start or end use `^` and `$`.

Files that are not matching any groups just ignored. If you want more visibility on them, create a group to match them all.

## Configuring workflow

In my example I prefer to use nexted workflows, to keep with conditions small.

You need to define job outputs. Each output number represent a workflow in the config file in order of their declaration.
Also, when you rn the workflow you could check mapping in the logs. The sample output is in action logs.

```yaml
jobs:
  detect_changed_files:
    runs-on: ubuntu-latest
    steps:
      - id: set_files_changed
        uses: cjkjvfnby/run_only_needed_actions@v1
        with:
             config_file: ".github/workflows/config.toml"
    outputs:
      workflow_a: ${{ steps.set_files_changed.outputs.output_01 }}
      workflow_b: ${{ steps.set_files_changed.outputs.output_02 }}
      workflow_c: ${{ steps.set_files_changed.outputs.output_03 }}
```

For your jobs you need to specify dependency (`needs`) and condition (`if`).

```yaml
  job_c:
    needs: detect_changed_files
    if: ${{ needs.detect_changed_files.outputs.workflow_c == 'true' }}
    uses: ./.github/workflows/_nested_workflow.yml
```

## Testing config on your repository

Add action without outputs, run it and check the sample of output in the logs.

That's it.  Enjoy the time saved on GitHub actions.

[1]: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#onpushpull_requestpull_request_targetpathspaths-ignore
[config_toml]: https://github.com/Cjkjvfnby/run_only_needed_actions/blob/master/check_file_changed/config.toml
[workflow]: https://github.com/Cjkjvfnby/run_only_needed_actions/blob/master/.github/workflows/run_on_push_v1.yml
[re]: https://docs.python.org/3/library/re.html#regular-expression-syntax
[re.search]: https://docs.python.org/3/library/re.html?highlight=re%20search#re.search

# Development

## Install dev requirements
```shell
pip install -r requirements-dev.txt
```

## Install library in editable mode
```shell
pip install -e .
```

## Install pre-commit
- add hooks
  ```shell
  pre-commit install
  pre-commit install --hook-type commit-msg
  ```
- update to the latest versions
  ```shell
  pre-commit autoupdate
  ```

## Formatting and Linting
```shell
pre-commit run --all-files
```

## Run test
```shell
pytest --cov=check_file_changed._file_checker --cov-report html
```
