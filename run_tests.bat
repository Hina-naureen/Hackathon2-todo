@echo off
:: run_tests.bat — Run backend test suite (Windows)
:: Requires: uv installed (https://docs.astral.sh/uv/)
cd /d "%~dp0backend"
uv run pytest tests/ -v
