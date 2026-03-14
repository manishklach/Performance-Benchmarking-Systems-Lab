param(
    [string]$Python = "python",
    [string]$Name = "amd-apu-monitor"
)

$ErrorActionPreference = "Stop"

Write-Host "Installing packaging dependency..."
& $Python -m pip install pyinstaller

Write-Host "Building standalone executable..."
& $Python -m PyInstaller `
    --noconfirm `
    --windowed `
    --name $Name `
    --collect-all matplotlib `
    --hidden-import tkinter `
    --paths src `
    src\amd_apu_toolkit\app_gui_entry.py

Write-Host "Build finished. Output is in dist\\$Name"
