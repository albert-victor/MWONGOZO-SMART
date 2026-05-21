# Start Mwongozo Smart (kills stale listeners on port 8000 first)
$ErrorActionPreference = "SilentlyContinue"
$port = 8000
$root = Split-Path -Parent $PSScriptRoot

Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

Start-Sleep -Milliseconds 500

$env:MWONGOZO_CATALOGUE_SEED_ON_STARTUP = "0"
Set-Location $root
Write-Host "Starting Mwongozo Smart at http://127.0.0.1:$port" -ForegroundColor Cyan
python -m uvicorn main:app --host 127.0.0.1 --port $port --reload
