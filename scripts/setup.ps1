# Crea el entorno virtual de Python e instala las dependencias del laboratorio.
# Uso:  powershell -ExecutionPolicy Bypass -File scripts/setup.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

Write-Host "== 1. Entorno virtual ==" -ForegroundColor Cyan
if (Test-Path ".venv") {
    Write-Host "El entorno .venv ya existe; se reutiliza."
} else {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        py -3.12 -m venv .venv
    } else {
        python -m venv .venv
    }
    Write-Host "Entorno .venv creado."
}

$python = Join-Path $root ".venv\Scripts\python.exe"
& $python -m pip install --upgrade pip --quiet
& $python -m pip install -r requirements.txt

Write-Host "== 2. Archivo .env ==" -ForegroundColor Cyan
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host ".env creado a partir de .env.example"
} else {
    Write-Host ".env ya existe; no se sobrescribe."
}

Write-Host "`nListo. Siguiente paso: scripts/start_lab.ps1" -ForegroundColor Green
