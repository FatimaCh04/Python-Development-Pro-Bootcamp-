# start.ps1 — Start the VAULT backend
# Uses Python 3.14 from python.org (properly installed, not the Store stub)

$python = "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe"

if (-not (Test-Path $python)) {
    Write-Error "Python 3.14 not found at $python"
    Write-Host "Trying py launcher fallback..."
    $python = (& where.exe python 2>$null | Select-Object -First 1)
}

if (-not $python -or -not (Test-Path $python)) {
    Write-Error "No usable Python found. Install Python from https://python.org"
    exit 1
}

Write-Host "Python: $python"
Write-Host "Dir:    $PSScriptRoot"

Set-Location $PSScriptRoot

# Install deps if needed
& $python -m pip install fastapi uvicorn[standard] cryptography pydantic pyperclip python-dotenv --quiet

# Start server (no --reload to avoid Store Python stdio crash)
& $python -m uvicorn main:app --host 127.0.0.1 --port 8000
