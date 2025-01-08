# Code Linting and Type Checking TODOs

## Line Length Issues (E501)
- [ ] `alfie/dirhelper.py:95` - Reduce line length (93 > 88)
- [ ] `core/settings.py:129` - Reduce line length (91 > 88)
- [ ] `notion/agent/processor.py:58` - Reduce line length (168 > 88)
- [ ] `notion/agent/processor.py:62` - Reduce line length (96 > 88)
- [ ] `notion/agent/processor.py:66` - Reduce line length (148 > 88)
- [ ] `notion/agent/tools/create.py:26` - Reduce line length (91 > 88)
- [ ] `notion/agent/tools/create.py:43` - Reduce line length (109 > 88)
- [ ] `notion/agent/tools/edit.py:51` - Reduce line length (96 > 88)
- [ ] `notion/agent/tools/v2_edit.py:96` - Reduce line length (119 > 88)
- [ ] `notion/agent1.py:51` - Reduce line length (93 > 88)
- [ ] `projects/create_project.py:3` - Reduce line length (90 > 88)
- [ ] `projects/github/setup.py:348` - Reduce line length (101 > 88)
- [ ] `projects/github/setup.py:361` - Reduce line length (97 > 88)
- [ ] `projects/github/setup.py:530` - Reduce line length (89 > 88)
- [ ] `projects/templates/django/core/settings.py:116` - Reduce line length (91 > 88)
- [ ] `system/coder_system.py:1` - Reduce line length (137 > 88)

## Unused Variables (F841)
- [ ] `alfie/dirhelper.py:98` - Remove or use `is_git` variable
- [ ] `projects/create_project.py:133` - Remove or use `f` variable
- [ ] `projects/dirhelper.py:64` - Remove or use `is_git` variable
- [ ] `projects/github/tests/test_git_service.py:33` - Remove or use `git` variable
- [ ] `projects/services.py:44` - Remove or use `f` variable
- [ ] `system/vscode/test.py:24` - Remove or use `count` variable
- [ ] `system/vscode/test.py:27` - Remove or use `really_long_string` variable
- [ ] `system/vscode/test.py:30` - Remove or use `unused_var` variable
- [ ] `tests/test_notion_agent_v2.py:85` - Remove or use `content` variable
- [ ] `tests/test_notion_agent_v2.py:158` - Remove or use `request` variable

## Import Formatting (I001)
- [ ] `notion/tests/test_tools.py:1` - Sort and format import block

## Variable Naming (N806)
- [ ] `tests/test_cli.py:52` - Rename `MockAgent` to lowercase in function
- [ ] `tests/test_cli.py:79` - Rename `MockAgent` to lowercase in function
- [ ] `tests/test_cli.py:105` - Rename `MockAgent` to lowercase in function

## Type Annotation Issues
- [ ] `notion/agent/base.py:40` - Add type annotation for `tools` (dict)
- [ ] `notion/agent/base.py:59` - Fix return type from `Any` to `AgentResponse`
- [ ] `notion/cli/commands.py:72` - Add missing `api_key` argument to `AgentConfig`
- [ ] `notion/cli/commands.py:75` - Fix incompatible type `AgentConfig` (expected `NotionService`)
- [ ] `tests/test_cli.py:48` - Add missing `message` argument to `AgentResponse`
- [ ] `tests/test_cli.py:77` - Add missing `message` and `data` arguments to `AgentResponse`
- [ ] `tests/test_cli.py:103` - Add missing `message` and `data` arguments to `AgentResponse`
- [ ] `tests/test_agent.py:58` - Add missing `api_key` argument to `AgentConfig`
- [ ] `tests/test_agent.py:59` - Fix incompatible type `AgentConfig` (expected `NotionService`)
- [ ] `projects/templates/django/core/urls.py:28` - Add type annotation to `redirect_to_admin` function

## Missing Imports/Stubs
- [ ] `notion/tests/test_tools.py:3` - Fix missing import for `agents.tools.code_tools`

## Configuration Updates Needed
- [ ] Update deprecated top-level linter settings in `pyproject.toml`:
  - Move `ignore` to `lint.ignore`
  - Move `select` to `lint.select`
