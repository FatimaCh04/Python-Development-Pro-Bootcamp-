Add-Type -AssemblyName System.IO.Compression.FileSystem
$src = "c:\Users\Shahab Computer's\Documents\GitHub\Python-Development-Pro-Bootcamp-\CipherVault\vault-frontend.zip"
$dst = "c:\Users\Shahab Computer's\Documents\GitHub\Python-Development-Pro-Bootcamp-\CipherVault\vault-frontend"
$out = "c:\Users\Shahab Computer's\Documents\GitHub\Python-Development-Pro-Bootcamp-\CipherVault\extract_output.txt"

$lines = @()
$lines += "=== FILES IN ZIP ==="
$zip = [System.IO.Compression.ZipFile]::OpenRead($src)
foreach ($entry in $zip.Entries) {
    $lines += $entry.FullName
}
$zip.Dispose()
$lines += ""
$lines += "=== EXTRACTING ==="
if (Test-Path $dst) {
    Remove-Item $dst -Recurse -Force
}
[System.IO.Compression.ZipFile]::ExtractToDirectory($src, $dst)
$lines += "Extraction complete to: $dst"
$lines += ""
$lines += "=== EXTRACTED FILE TREE ==="
Get-ChildItem -Path $dst -Recurse | ForEach-Object {
    $lines += $_.FullName.Replace($dst, "")
}
$lines | Out-File -FilePath $out -Encoding UTF8
Write-Host "Done. Output written to $out"
