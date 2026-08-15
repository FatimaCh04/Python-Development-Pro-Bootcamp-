# run_tests.ps1 — Run the pytest test suite

$python = "$env:LOCALAPPDATA\Programs\Python\Python314\python.exe"

if (-not (Test-Path $python)) {
    Write-Error "Python 3.14 not found at $python"
    exit 1
}

Set-Location $PSScriptRoot

Write-Host "Installing pytest..."
& $python -m pip install pytest --quiet

Write-Host "`nRunning test suite...`n"
& $python -m pytest test_vault.py -v --tb=short

Write-Host "`nTest run complete."
