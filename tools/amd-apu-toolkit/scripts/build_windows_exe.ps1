param(
    [string]$Python = "python",
    [string]$Name = "amd-apu-monitor",
    [string]$VenvPath = ".build-venv"
)

$ErrorActionPreference = "Stop"

$venvPython = Join-Path $VenvPath "Scripts\\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating isolated build venv at $VenvPath ..."
    & $Python -m venv $VenvPath
}

Write-Host "Installing build dependencies into isolated venv..."
& $venvPython -m pip install --upgrade pip setuptools wheel
& $venvPython -m pip install -e .
& $venvPython -m pip install pyinstaller

Write-Host "Building standalone executable..."
& $venvPython -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name $Name `
    --collect-all matplotlib `
    --collect-data amd_apu_toolkit `
    --hidden-import tkinter `
    --paths src `
    src\amd_apu_toolkit\app_gui_entry.py

Write-Host "Build finished. Output is in dist\\$Name"
