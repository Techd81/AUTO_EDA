# Repository Guidelines

## Project Structure & Module Organization
`src/auto_eda/` contains the runtime package. Put shared server scaffolding, process helpers, and error types in `src/auto_eda/core/`; reusable data models in `src/auto_eda/models/`; and EasyEDA-specific bridge, tool handlers, component tables, and flows in `src/auto_eda/servers/easyeda/`. Tests mirror the package layout under `tests/` with focused areas such as `tests/test_core/` and `tests/test_servers/test_easyeda/`. Treat `analysis/` and `research/` as supporting design notes, not runtime code. Use `mcp.json.example` as the starting point for local MCP configuration.

## Build, Test, and Development Commands
`pip install -e ".[dev]"` installs the package with pytest, coverage, Ruff, and mypy.
`python -m auto_eda easyeda` starts the EasyEDA MCP server locally.
`auto-eda easyeda` runs the same entry point through the console script.
`pytest` runs the full suite.
`pytest -m "not integration"` skips tests that require real EDA tooling.
`pytest --cov=src/auto_eda --cov-report=term-missing` checks coverage.
`ruff check .` runs lint and import-order checks.
`mypy src` enforces the repository’s strict typing rules.

## Coding Style & Naming Conventions
Use 4-space indentation, type hints on public code, and keep lines near the Ruff limit of 100 characters. Follow existing Python naming: `snake_case` for modules, functions, and variables; `PascalCase` for classes; and `*Input` / `*Result` Pydantic models for MCP tool contracts. Keep MCP tool functions thin and move reusable logic into feature modules such as `stm32_flow.py` or shared helpers in `core/`.

## Testing Guidelines
Write pytest files as `test_<module>.py` and keep them close to the matching feature area. Mark async tests with `@pytest.mark.asyncio`. Mock bridge or external EDA behavior rather than relying on a live EasyEDA instance, following `tests/test_servers/test_easyeda/test_stm32_flow.py`. The configured coverage floor is 60%; contributors should fully cover new public behavior and aim for 80%+ on touched modules.

## Commit & Pull Request Guidelines
Recent history follows Conventional Commits, for example `feat(easyeda): ...`, `fix: ...`, and `docs: ...`. Keep commit subjects short, imperative, and scoped when useful. Pull requests should summarize the user-visible change, list verification commands, link related issues, and include screenshots or bridge/export evidence when UI-facing EasyEDA flows change.

## Configuration & Safety Notes
Do not commit machine-specific output paths, local bridge settings, or credentials. Keep workstation overrides in untracked files and copy from `mcp.json.example` when setting up a new environment.
