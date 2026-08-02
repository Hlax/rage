[CmdletBinding()]
param(
    [ValidateRange(1, 1000)]
    [int]$BenchmarkRuns = 25
)

# Mock-only internal MVP launcher. This script never enables live LLM, source
# network, paid-cloud, or private API services.
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$DefaultResearchPrompt = "Does AI improve creative output while reducing diversity?"
$WorkDir = "data/tmp/researcher_product_proof_work"
$ArtifactPath = "data/reports/researcher_product_proof_latest.json"
$PreviewUrl = "http://localhost:3000/atlas-preview"

Set-Location $RepoRoot
$env:RGE_LLM_MODE = "mock"
$env:RGE_ALLOW_LIVE_LLM = "0"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python is required. Install Python or add python.exe to PATH, then run this launcher again."
}

Write-Host "Internal MVP launch profile: mock-only"
Write-Host "Default research prompt: $DefaultResearchPrompt"
Write-Host "Running researcher product proof..."

& python -m rge.cli prove-researcher-product `
    --work-dir $WorkDir `
    --artifact-out $ArtifactPath `
    --topic $DefaultResearchPrompt `
    --domain creativity `
    --benchmark-runs $BenchmarkRuns

if ($LASTEXITCODE -ne 0) {
    throw "Researcher product proof command failed with exit code $LASTEXITCODE."
}

if (-not (Test-Path -LiteralPath $ArtifactPath -PathType Leaf)) {
    throw "Researcher product proof did not write the expected artifact: $ArtifactPath"
}

$Proof = Get-Content -Raw -LiteralPath $ArtifactPath | ConvertFrom-Json
$ProductVerdict = [string]$Proof.product_verdict
Write-Host "product_verdict: $ProductVerdict"

if ($ProductVerdict -ne "GO") {
    throw "Internal MVP launch blocked: expected product_verdict GO, received '$ProductVerdict'."
}

if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
    throw "Node.js and npm are required to start the Atlas preview."
}

$SiteRoot = Join-Path $RepoRoot "apps/public-site"
Set-Location $SiteRoot

if (-not (Test-Path -LiteralPath "node_modules" -PathType Container)) {
    Write-Host "Installing public-site dependencies (first launch only)..."
    & npm install
    if ($LASTEXITCODE -ne 0) {
        throw "npm install failed with exit code $LASTEXITCODE."
    }
}

Write-Host "Starting the read-only Atlas preview at $PreviewUrl"
Write-Host "No service will be started on port 8000. Press Ctrl+C to stop the preview."
& npm run dev -- --hostname 127.0.0.1 --port 3000

if ($LASTEXITCODE -ne 0) {
    throw "Atlas preview exited with code $LASTEXITCODE."
}
