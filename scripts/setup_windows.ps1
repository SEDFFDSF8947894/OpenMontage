# Windows setup for OpenMontage. Run from repository root:
# powershell -ExecutionPolicy Bypass -File .\scripts\setup_windows.ps1
# Does not submit paid generation requests.
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
function Require-Command([string]$Name) {
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Missing $Name. Install it, restart PowerShell, and rerun."
  }
}
Require-Command 'py'
Require-Command 'node'
Require-Command 'npm'
Require-Command 'ffmpeg'
Require-Command 'ffprobe'
& py -3 -c 'import sys; assert sys.version_info >= (3,10), "Python 3.10+ required"'
if ($LASTEXITCODE -ne 0) { throw 'Python 3.10+ required' }
$nodeVersion = (& node --version).Trim().TrimStart('v').Split('.')
$major = [int]$nodeVersion[0]; $minor = [int]$nodeVersion[1]; $patch = [int]$nodeVersion[2]
if (-not (($major -eq 22 -and ($minor -gt 23 -or ($minor -eq 23 -and $patch -ge 4))) -or ($major -eq 24 -and ($minor -gt 22 -or ($minor -eq 22 -and $patch -ge 1))) -or ($major -eq 26 -and ($minor -gt 12 -or ($minor -eq 12 -and $patch -ge 1))))) {
  throw 'Unsupported Node version. Use patched Node 22.23.4+, 24.22.1+, or 26.12.1+.'
}
if (-not (Test-Path '.venv\Scripts\python.exe')) { & py -3 -m venv .venv; if ($LASTEXITCODE -ne 0) { throw 'venv creation failed' } }
$python = (Resolve-Path '.venv\Scripts\python.exe').Path
& $python -m pip install --upgrade 'pip>=26.2.2'
if ($LASTEXITCODE -ne 0) { throw 'pip upgrade failed' }
& $python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Python dependencies failed' }
Push-Location remotion-composer
try { & npm install; if ($LASTEXITCODE -ne 0) { throw 'npm install failed' } }
finally { Pop-Location }
if (-not (Test-Path '.env')) { Copy-Item '.env.example' '.env' }
Write-Host 'Setup complete. Configure .env locally; NEVER commit API keys.'
& $python scripts/production_readiness.py
if ($LASTEXITCODE -ne 0) { throw 'Readiness checks failed; review JSON output.' }
Write-Host 'Ready for local pipeline preflight. This is not an end-to-end render test.'
