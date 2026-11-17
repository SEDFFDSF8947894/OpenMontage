# Install native desktop UI and create Windows shortcut (does not make paid API calls).
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$python = Join-Path (Get-Location) '.venv\Scripts\python.exe'
$pythonw = Join-Path (Get-Location) '.venv\Scripts\pythonw.exe'
if (-not (Test-Path $python)) { throw 'Run scripts/setup_windows.ps1 first.' }
& $python -m pip install -r desktop_studio/requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Desktop dependencies installation failed.' }
if (-not (Test-Path $pythonw)) { throw 'pythonw.exe not found in virtual environment.' }
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut((Join-Path $desktop 'OpenMontage Pro Studio.lnk'))
$shortcut.TargetPath = $pythonw
$shortcut.Arguments = '-m desktop_studio'
$shortcut.WorkingDirectory = (Get-Location).Path
$shortcut.Description = 'OpenMontage Pro Studio native desktop application'
$shortcut.Save()
Write-Host "Desktop shortcut created: $desktop\OpenMontage Pro Studio.lnk"
Write-Host 'Double-click the shortcut to open the native desktop window (no browser).'
