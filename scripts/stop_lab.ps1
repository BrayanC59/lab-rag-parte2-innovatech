# Detiene el laboratorio. Los volumenes se conservan salvo que se use -Clean.
param([switch]$Clean)

$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

docker compose down
if ($Clean) {
    Write-Host "Eliminando volumenes del laboratorio ..." -ForegroundColor Yellow
    docker compose down -v
}
