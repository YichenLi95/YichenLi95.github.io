Set-Location $PSScriptRoot
Write-Host "Starting LOCUST starter project at http://127.0.0.1:4173/"
$py = 'C:\Users\liyic\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
& $py -m http.server 4173 --bind 127.0.0.1 --directory (Join-Path $PSScriptRoot 'site')
