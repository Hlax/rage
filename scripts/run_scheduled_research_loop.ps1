# Local-safe scheduled research loop (Windows Task Scheduler)
# Profile: local_mock_daily — mock LLM only; blocks live network/LLM/paid APIs.
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
$env:RGE_LLM_MODE = "mock"
python scripts/run_scheduled_research_loop.py @args
exit $LASTEXITCODE
